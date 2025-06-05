#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import time
from typing import Any, Dict, List

from config import (DEFAULT_MAX_PAGES, DEFAULT_MAX_RETRIES,
                    DEFAULT_RETRY_BASE_DELAY, GEMINI_MODEL)

try:
    import google.generativeai as genai
    from PIL import Image
except ImportError as e:
    print(f"Missing required packages. Please install them:")
    print("pip3 install google-generativeai")
    exit(1)


class MetadataExtractor:
    """Extracts title, author, and year from PDF images using Gemini AI"""

    def __init__(self, api_key: str):
        """Initialize Gemini API client"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def _create_extraction_prompt(self) -> str:
        """Generate prompt for AI metadata extraction"""
        return """
        Analyze this academic paper/document and extract the following information in JSON format:
        
        {
            "title": "Full title of the paper/article",
            "author": "Author name(s) - include all authors if multiple",
            "year": "Year of publication",
            "source_filename": "The filename this data was extracted from"
        }
        
        Instructions:
        - Look for the title, usually prominently displayed at the top
        - Find author information, which might be below the title or in a byline
        - Look for publication year, which might be in various formats (©2015, 2015, etc.)
        - If multiple authors, include all of them
        - If you cannot find specific information, use "Not found" for that field
        - Return only valid JSON, no additional text
        
        Analyze carefully and extract the most accurate information possible.
        """

    def _prepare_image_content(
        self, images: List[Image.Image], pdf_processor, max_pages: int = None
    ) -> List[Dict[str, str]]:
        """Convert images to base64 format for API submission"""
        image_parts = []
        # Limit images to reduce API costs
        num_images = (
            max_pages if max_pages is not None else min(len(images), DEFAULT_MAX_PAGES)
        )
        for image in images[:num_images]:
            data, mime_type = pdf_processor.image_to_base64(image)
            image_parts.append({"mime_type": mime_type, "data": data})
        return image_parts

    def _parse_api_response(self, response, filename: str) -> Dict[str, Any]:
        """Parse and validate JSON response from Gemini API"""
        try:
            response_text = response.text.strip()

            # Clean markdown code block formatting
            response_text = re.sub(
                r"^```\s*json\s*\n?", "", response_text, flags=re.IGNORECASE
            )
            response_text = re.sub(r"\n?```\s*$", "", response_text)
            response_text = response_text.strip()

            # Extract JSON from response text
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                response_text = response_text[start:end]

            result = json.loads(response_text)

            if not isinstance(result, dict):
                return self._create_fallback_response(filename, str(result))

            # Ensure all required fields are present
            required_fields = ["title", "author", "year"]
            for field in required_fields:
                if field not in result:
                    result[field] = "Not found"

            result["source_filename"] = filename
            return result

        except json.JSONDecodeError as e:
            return self._create_fallback_response(filename, response.text, str(e))
        except Exception as e:
            return self._create_fallback_response(
                filename, response.text, f"Unexpected error: {str(e)}"
            )

    def _create_fallback_response(
        self, filename: str, raw_response: str, error: str = None
    ) -> Dict[str, Any]:
        """Create response when JSON parsing fails"""
        return {
            "title": "Could not parse JSON response",
            "author": "Could not parse JSON response",
            "year": "Could not parse JSON response",
            "source_filename": filename,
            "raw_response": (
                raw_response[:500] + "..." if len(raw_response) > 500 else raw_response
            ),
            "parse_error": error,
        }

    def _create_error_response(
        self, error_message: str, filename: str
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "title": "Error",
            "author": "Error",
            "year": "Error",
            "source_filename": filename,
            "error": error_message,
        }

    def _is_rate_limit_error(self, error_str: str) -> bool:
        """Check if error is due to API rate limiting"""
        return (
            "429" in error_str
            or "quota" in error_str.lower()
            or "rate" in error_str.lower()
        )

    def _is_transient_error(self, error_str: str) -> bool:
        """Check if error is temporary and worth retrying"""
        transient_indicators = [
            "timeout",
            "connection",
            "network",
            "temporary",
            "unavailable",
            "service",
            "502",
            "503",
            "504",
            "gateway",
        ]
        error_lower = error_str.lower()
        return any(indicator in error_lower for indicator in transient_indicators)

    def extract_metadata_from_images(
        self,
        images: List[Image.Image],
        filename: str,
        pdf_processor,
        max_pages: int = None,
    ) -> Dict[str, Any]:
        """Main method to extract metadata from PDF images with retry logic"""
        if not images:
            return self._create_error_response("No images to process", filename)

        prompt = self._create_extraction_prompt()
        max_retries = DEFAULT_MAX_RETRIES
        base_delay = DEFAULT_RETRY_BASE_DELAY

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                image_parts = self._prepare_image_content(
                    images, pdf_processor, max_pages
                )
                content_parts = image_parts + [{"text": prompt}]
                response = self.model.generate_content(content_parts)
                return self._parse_api_response(response, filename)

            except Exception as e:
                error_message = str(e)

                # Determine if error is retryable and calculate delay
                should_retry = False
                delay = 0

                if self._is_rate_limit_error(error_message):
                    should_retry = True
                    delay = base_delay * (2**attempt)
                    error_type = "Rate limit"
                elif self._is_transient_error(error_message):
                    should_retry = True
                    delay = min(5 * (2**attempt), 60)
                    error_type = "Transient error"

                if should_retry and attempt < max_retries - 1:
                    print(
                        f"⏳ {error_type} for {filename}. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}..."
                    )
                    time.sleep(delay)
                    continue
                elif should_retry:
                    return self._create_error_response(
                        f"{error_type} exceeded after {max_retries} attempts: {error_message}",
                        filename,
                    )
                else:
                    return self._create_error_response(
                        f"API call failed: {error_message}", filename
                    )

        return self._create_error_response(
            f"Failed after {max_retries} attempts", filename
        )
