#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import io
import os
from typing import List, Tuple

from config import DEFAULT_DPI, DEFAULT_MAX_PAGES

try:
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError as e:
    print(f"Missing required packages. Please install them:")
    print("pip3 install pdf2image pillow")
    print("Also install poppler-utils: brew install poppler")
    exit(1)


class PDFProcessor:
    """Converts PDF files to images for AI analysis"""

    def pdf_to_images(
        self, pdf_path: str, max_pages: int = DEFAULT_MAX_PAGES
    ) -> List[Image.Image]:
        """Convert PDF pages to PIL images for AI processing"""
        try:
            # Validate file exists and is readable
            if not os.path.exists(pdf_path):
                print(f"PDF file does not exist: {pdf_path}")
                return []

            if not os.access(pdf_path, os.R_OK):
                print(f"No read permission for PDF file: {pdf_path}")
                return []

            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                print(f"PDF file is empty: {pdf_path}")
                return []

            # Warn about large files that may be slow to process
            if file_size > 100 * 1024 * 1024:
                print(f"⚠️  Large PDF file ({file_size // (1024*1024)} MB): {pdf_path}")

            # Convert PDF pages to images using pdf2image
            images = convert_from_path(
                pdf_path, first_page=1, last_page=max_pages, dpi=DEFAULT_DPI
            )
            return images
        except PermissionError:
            print(f"Permission denied accessing PDF: {pdf_path}")
            return []
        except FileNotFoundError:
            print(f"PDF file not found: {pdf_path}")
            return []
        except Exception as e:
            # Handle specific PDF errors with user-friendly messages
            error_msg = str(e).lower()
            if "password" in error_msg or "encrypted" in error_msg:
                print(f"PDF is password protected or encrypted: {pdf_path}")
            elif "corrupted" in error_msg or "damaged" in error_msg:
                print(f"PDF file appears to be corrupted: {pdf_path}")
            else:
                print(f"Error converting PDF {pdf_path}: {e}")
            return []

    def _get_image_format(self, image: Image.Image) -> str:
        """Determine optimal image format based on image mode"""
        return "PNG" if image.mode in ("RGBA", "LA", "P") else "JPEG"

    def _get_mime_type(self, image_format: str) -> str:
        """Get MIME type for image format"""
        return "image/png" if image_format == "PNG" else "image/jpeg"

    def image_to_base64(self, image: Image.Image) -> Tuple[str, str]:
        """Convert PIL image to base64 string for API transmission"""
        buffer = io.BytesIO()
        image_format = self._get_image_format(image)

        # Save image to buffer with optimal format and compression

        if image_format == "PNG":
            image.save(buffer, format="PNG")
        else:
            image.save(buffer, format="JPEG", quality=85, optimize=True)

        image_bytes = buffer.getvalue()
        mime_type = self._get_mime_type(image_format)
        return base64.b64encode(image_bytes).decode(), mime_type
