#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
import io
import json
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from config import (DEFAULT_DPI,
                    DEFAULT_MAX_FILENAME_LENGTH, DEFAULT_MAX_PAGES,
                    DEFAULT_MAX_RETRIES, DEFAULT_OUTPUT_FILE,
                    DEFAULT_RATE_LIMIT_DELAY, DEFAULT_RETRY_BASE_DELAY,
                    GEMINI_MODEL, PDF_EXTENSIONS)

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError as e:
    print(f"Missing required packages. Please install them:")
    print("pip3 install pdf2image pillow google-generativeai python-dotenv")
    print("Also install poppler-utils: brew install poppler")
    exit(1)


class PDFMetadataExtractor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def update_results_file(
        self, results_file_path: str, new_result: Dict[str, Any]
    ) -> bool:
        try:
            os.makedirs(os.path.dirname(results_file_path), exist_ok=True)

            existing_results = []
            if os.path.exists(results_file_path):
                try:
                    with open(results_file_path, "r", encoding="utf-8") as f:
                        existing_results = json.load(f)
                    if not isinstance(existing_results, list):
                        existing_results = []
                except (json.JSONDecodeError, IOError):
                    existing_results = []

            existing_results.append(new_result)

            with open(results_file_path, "w", encoding="utf-8") as f:
                json.dump(existing_results, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"⚠️  Failed to update results file: {e}")
            return False

    def sanitize_filename(self, text: str) -> str:
        if not text or text == "Not found":
            return "Unknown"

        text = re.sub(r'[<>:"/\\|?*]', "", text)
        text = re.sub(r"\s+", " ", text.replace("\n", " "))
        text = re.sub(r"[†‡§¶#@$%^&*+={}[\]~`]", "", text)
        text = text.strip()[:DEFAULT_MAX_FILENAME_LENGTH]
        return text

    def create_new_filename(self, metadata: Dict[str, Any]) -> str:
        year = self.sanitize_filename(metadata.get("year", "Unknown"))

        author_raw = metadata.get("author", "Unknown")
        if isinstance(author_raw, list):
            author = str(author_raw[0]) if author_raw else "Unknown"
        else:
            author = str(author_raw)

        author = self.sanitize_filename(author)
        title = self.sanitize_filename(metadata.get("title", "Unknown"))

        if " and " in author:
            author = author.split(" and ")[0].strip()
        elif "," in author:
            author = author.split(",")[0].strip()

        new_filename = f"{year} - {author} - {title}.pdf"
        return new_filename

    def copy_pdf_file(
        self, source_path: str, metadata: Dict[str, Any], output_dir: str
    ) -> Dict[str, str]:
        try:
            source_file = Path(source_path)
            output_directory = Path(output_dir)

            output_directory.mkdir(exist_ok=True)

            new_filename = self.create_new_filename(metadata)
            output_path = output_directory / new_filename

            counter = 1
            original_output_path = output_path
            while output_path.exists():
                stem = original_output_path.stem
                output_path = output_directory / f"{stem} ({counter}).pdf"
                counter += 1

            shutil.copy2(str(source_file), str(output_path))
            return {
                "copied": True,
                "source_filename": source_file.name,
                "output_filename": output_path.name,
                "source_path": str(source_file),
                "output_path": str(output_path),
            }

        except Exception as e:
            return {
                "copied": False,
                "error": str(e),
                "source_filename": Path(source_path).name,
            }

    def pdf_to_images(
        self, pdf_path: str, max_pages: int = DEFAULT_MAX_PAGES
    ) -> List[Image.Image]:
        try:
            images = convert_from_path(
                pdf_path, first_page=1, last_page=max_pages, dpi=DEFAULT_DPI
            )
            return images
        except Exception as e:
            print(f"Error converting PDF {pdf_path}: {e}")
            return []

    def image_to_base64(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode()

    def extract_metadata_from_images(
        self, images: List[Image.Image], filename: str, max_pages: int = None
    ) -> Dict[str, Any]:
        if not images:
            return {"error": "No images to process"}

        prompt = """
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

        max_retries = DEFAULT_MAX_RETRIES
        base_delay = DEFAULT_RETRY_BASE_DELAY

        for attempt in range(max_retries):
            try:
                image_parts = []
                max_images = max_pages if max_pages is not None else min(len(images), DEFAULT_MAX_PAGES)
                for image in images[:max_images]:
                    image_parts.append(
                        {"mime_type": "image/png", "data": self.image_to_base64(image)}
                    )

                content = image_parts + [prompt]

                response = self.model.generate_content(content)

                try:
                    response_text = response.text.strip()

                    if response_text.startswith("```json"):
                        response_text = response_text[7:]
                    if response_text.endswith("```"):
                        response_text = response_text[:-3]

                    response_text = response_text.strip()

                    result = json.loads(response_text)
                    result["source_filename"] = filename
                    return result
                except json.JSONDecodeError as e:
                    return {
                        "title": "Could not parse JSON response",
                        "author": "Could not parse JSON response",
                        "year": "Could not parse JSON response",
                        "source_filename": filename,
                        "raw_response": response.text,
                        "parse_error": str(e),
                    }

            except Exception as e:
                error_str = str(e)

                if (
                    "429" in error_str
                    or "quota" in error_str.lower()
                    or "rate" in error_str.lower()
                ):
                    if attempt < max_retries - 1:
                        delay = base_delay * (2**attempt)
                        print(
                            f"⏳ Rate limit hit for {filename}. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}..."
                        )
                        time.sleep(delay)
                        continue
                    else:
                        return {
                            "error": f"Rate limit exceeded after {max_retries} attempts: {error_str}",
                            "source_filename": filename,
                        }
                else:
                    return {
                        "error": f"API call failed: {error_str}",
                        "source_filename": filename,
                    }

        return {
            "error": f"Failed after {max_retries} attempts",
            "source_filename": filename,
        }

    def process_pdf(
        self,
        pdf_path: str,
        output_dir: str = None,
        copy_files: bool = True,
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> Dict[str, Any]:
        print(f"Processing: {pdf_path}")

        filename = os.path.basename(pdf_path)

        images = self.pdf_to_images(pdf_path, max_pages)
        if not images:
            return {
                "error": "Failed to convert PDF to images",
                "source_filename": filename,
            }

        metadata = self.extract_metadata_from_images(images, filename, max_pages)

        if copy_files and output_dir and "error" not in metadata:
            copy_result = self.copy_pdf_file(pdf_path, metadata, output_dir)
            metadata["copy_info"] = copy_result

            if copy_result.get("copied"):
                metadata["output_filename"] = copy_result["output_filename"]
                print(f"📝 Copied: {filename} → {copy_result['output_filename']}")

        return metadata

    def process_directory(
        self,
        directory_path: str,
        output_dir: str = None,
        results_file_path: str = None,
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> List[Dict[str, Any]]:
        results = []
        directory = Path(directory_path)
        pdf_files = []
        for pattern in PDF_EXTENSIONS:
            pdf_files.extend(directory.glob(pattern))

        if not pdf_files:
            print(f"No PDF files found in {directory_path}")
            return results

        print(f"🔍 Found {len(pdf_files)} PDF files to process")
        if output_dir:
            print(f"📁 Output directory: {os.path.abspath(output_dir)}")
        else:
            print("📄 Metadata extraction only (no file copying)")

        if results_file_path:
            print(
                f"💾 Results will be saved incrementally to: {os.path.abspath(results_file_path)}"
            )

        print(
            f"⏰ Rate limiting: {DEFAULT_RATE_LIMIT_DELAY} seconds between API calls to respect Gemini's rate limits"
        )

        for i, pdf_file in enumerate(pdf_files, 1):
            print(
                f"\n🔄 Processing file {i}/{len(pdf_files)} at {datetime.now().strftime('%H:%M:%S')}"
            )

            copy_files = output_dir is not None
            result = self.process_pdf(str(pdf_file), output_dir, copy_files, max_pages)
            results.append(result)

            if results_file_path:
                if self.update_results_file(results_file_path, result):
                    print(f"📝 Result saved to {os.path.basename(results_file_path)}")
                else:
                    print(
                        f"⚠️  Failed to save result for {result.get('source_filename', 'unknown file')}"
                    )

            if i < len(pdf_files):
                if "error" not in result:
                    print(
                        f"⏳ Waiting {DEFAULT_RATE_LIMIT_DELAY} seconds to respect API rate limits..."
                    )
                    time.sleep(DEFAULT_RATE_LIMIT_DELAY)

        return results


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Extract metadata from PDF files using Google Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 pdf_metadata_extractor.py /path/to/pdfs /path/to/output
  python3 pdf_metadata_extractor.py ./data ./output --max-pages 1
  python3 pdf_metadata_extractor.py /docs /results --no-copy
        """,
    )

    parser.add_argument(
        "source",
        help="Source directory containing PDF files",
    )

    parser.add_argument(
        "output",
        help="Output directory for renamed files",
    )

    parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Only extract metadata, do not copy files",
    )

    parser.add_argument(
        "--max-pages",
        "-p",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"Maximum number of pages to analyze per PDF (default: {DEFAULT_MAX_PAGES})",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    if args.max_pages < 1:
        print("❌ ERROR: --max-pages must be at least 1")
        return
    if args.max_pages > 10:
        print("⚠️  WARNING: --max-pages > 10 may be slow and expensive for API costs")
        try:
            confirm = input("Continue anyway? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print("Operation cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found")
        print("Please create a .env file with: GEMINI_API_KEY=your-actual-api-key")
        return

    try:
        extractor = PDFMetadataExtractor(api_key)
        print("🔑 Gemini API connection established")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini API: {e}")
        print("Check your API key and internet connection")
        return

    source_dir = os.path.abspath(args.source)
    output_dir = os.path.abspath(args.output)

    if not os.path.exists(source_dir):
        print(f"❌ Source directory {source_dir} does not exist")
        return

    print("🚀 Starting PDF metadata extraction...")
    print(f"📁 Source directory: {source_dir}")
    if not args.no_copy:
        print(f"📂 Output directory: {output_dir}")
    else:
        print("📄 Metadata extraction only (no file copying)")
    print(f"📄 Analyzing first {args.max_pages} pages of each PDF")

    results_file_path = os.path.join(output_dir, DEFAULT_OUTPUT_FILE)

    results = extractor.process_directory(
        source_dir,
        output_dir if not args.no_copy else None,
        results_file_path,
        args.max_pages,
    )

    if not results:
        print("❌ No PDF files found or processed successfully")
        return

    print("\n" + "=" * 80)
    print("📊 EXTRACTION RESULTS")
    print("=" * 80)

    successful_extractions = 0
    copied_files = 0
    for i, result in enumerate(results, 1):
        print(f"\n{i}. 📄 File: {result.get('source_filename', 'Unknown')}")
        print("-" * 60)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            successful_extractions += 1
            print(f"📖 Title:  {result.get('title', 'Not found')}")
            print(f"👤 Author: {result.get('author', 'Not found')}")
            print(f"📅 Year:   {result.get('year', 'Not found')}")

            if not args.no_copy:
                copy_info = result.get("copy_info", {})
                if copy_info.get("copied"):
                    copied_files += 1
                    print(f"📝 Copied to: {copy_info['output_filename']}")
                elif "error" in copy_info:
                    print(f"⚠️  Copy failed: {copy_info['error']}")

    print(f"\n✅ Successfully processed {successful_extractions}/{len(results)} files")
    if not args.no_copy:
        print(f"📝 Copied {copied_files} files to output directory")

    if results_file_path:
        print(f"💾 All results saved incrementally to: {results_file_path}")

    print("\n🎉 Processing complete!")


if __name__ == "__main__":
    main()
