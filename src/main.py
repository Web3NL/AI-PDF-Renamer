#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from config import (DEFAULT_MAX_PAGES, DEFAULT_OUTPUT_FILE,
                    DEFAULT_RATE_LIMIT_DELAY, PDF_EXTENSIONS)
from file_manager import FileManager
from metadata_extractor import MetadataExtractor
from pdf_processor import PDFProcessor

try:
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required packages. Please install them:")
    print("pip3 install python-dotenv")
    exit(1)


class PDFMetadataExtractor:
    """Main orchestrator for PDF metadata extraction and file management"""

    def __init__(self, api_key: str):
        """Initialize all processing components"""
        self.pdf_processor = PDFProcessor()
        self.metadata_extractor = MetadataExtractor(api_key)
        self.file_manager = FileManager()

    def _create_error_response(
        self, error_message: str, filename: str
    ) -> Dict[str, Any]:
        """Create standardized error response for processing failures"""
        return {
            "title": "Error",
            "author": "Error",
            "year": "Error",
            "source_filename": filename,
            "error": error_message,
        }

    def process_pdf(
        self,
        pdf_path: str,
        output_dir: str = None,
        copy_files: bool = True,
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> Dict[str, Any]:
        """Process single PDF file: extract metadata and optionally copy with new name"""
        # Validate input parameters
        if not pdf_path or not isinstance(pdf_path, str):
            return self._create_error_response("Invalid PDF path provided", "unknown")

        if max_pages < 1:
            return self._create_error_response(
                "max_pages must be at least 1", os.path.basename(pdf_path)
            )

        if copy_files and output_dir and not isinstance(output_dir, str):
            return self._create_error_response(
                "Invalid output directory provided", os.path.basename(pdf_path)
            )

        print(f"Processing: {pdf_path}")
        filename = os.path.basename(pdf_path)

        # Convert PDF to images for AI analysis

        images = self.pdf_processor.pdf_to_images(pdf_path, max_pages)
        if not images:
            return self._create_error_response(
                "Failed to convert PDF to images", filename
            )

        # Extract metadata using AI
        metadata = self.metadata_extractor.extract_metadata_from_images(
            images, filename, self.pdf_processor, max_pages
        )

        # Copy file with new name if requested and extraction succeeded
        if copy_files and output_dir and "error" not in metadata:
            copy_result = self.file_manager.copy_pdf_file(
                pdf_path, metadata, output_dir
            )
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
        """Process all PDF files in a directory with rate limiting and progress tracking"""
        # Validate input parameters
        if not directory_path or not isinstance(directory_path, str):
            print("❌ ERROR: Invalid directory path provided")
            return []

        if max_pages < 1:
            print("❌ ERROR: max_pages must be at least 1")
            return []

        # Validate directory exists and is accessible
        directory = Path(directory_path)
        if not directory.exists():
            print(f"❌ ERROR: Directory does not exist: {directory_path}")
            return []

        if not directory.is_dir():
            print(f"❌ ERROR: Path is not a directory: {directory_path}")
            return []

        if not os.access(directory_path, os.R_OK):
            print(f"❌ ERROR: No read permission for directory: {directory_path}")
            return []

        # Find all PDF files in directory
        results = []
        try:
            pdf_extensions = [ext.replace("*", "") for ext in PDF_EXTENSIONS]
            pdf_files = []
            for f in directory.iterdir():
                if f.is_file() and f.suffix.lower() in [
                    ext.lower() for ext in pdf_extensions
                ]:
                    pdf_files.append(f)
        except PermissionError:
            print(f"❌ ERROR: Permission denied accessing directory: {directory_path}")
            return []
        except Exception as e:
            print(f"❌ ERROR: Failed to scan directory {directory_path}: {e}")
            return []

        if not pdf_files:
            print(f"No PDF files found in {directory_path}")
            return results

        # Display processing summary
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

        # Process each PDF file with rate limiting
        for i, pdf_file in enumerate(pdf_files, 1):
            processing_start = time.time()
            print(
                f"\n🔄 Processing file {i}/{len(pdf_files)} at {datetime.now().strftime('%H:%M:%S')}"
            )

            # Process individual file
            copy_files = output_dir is not None
            result = self.process_pdf(str(pdf_file), output_dir, copy_files, max_pages)
            results.append(result)

            # Save result incrementally if file specified
            if results_file_path:
                if self.file_manager.update_results_file(results_file_path, result):
                    print(f"📝 Result saved to {os.path.basename(results_file_path)}")
                else:
                    print(
                        f"⚠️  Failed to save result for {result.get('source_filename', 'unknown file')}"
                    )

            # Rate limiting: wait between successful API calls
            if i < len(pdf_files) and "error" not in result:
                processing_time = time.time() - processing_start
                remaining_delay = max(0, DEFAULT_RATE_LIMIT_DELAY - processing_time)
                if remaining_delay > 0:
                    print(
                        f"⏳ Waiting {remaining_delay:.1f} more seconds to respect API rate limits..."
                    )
                    time.sleep(remaining_delay)

        return results


def parse_arguments():
    """Parse command line arguments for the application"""
    parser = argparse.ArgumentParser(
        description="Extract metadata from PDF files using Google Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py /path/to/pdfs /path/to/output
  python3 main.py ./data ./output --max-pages 1
  python3 main.py /docs /results --no-copy
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

    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip interactive confirmations (for automation)",
    )

    return parser.parse_args()


def main():
    """Main entry point for the PDF metadata extractor"""
    args = parse_arguments()

    # Validate max_pages parameter
    if args.max_pages < 1:
        print("❌ ERROR: --max-pages must be at least 1")
        return
    # Warn about potentially expensive operations
    if args.max_pages > 10 and not args.force:
        print("⚠️  WARNING: --max-pages > 10 may be slow and expensive for API costs")
        try:
            confirm = input("Continue anyway? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print("Operation cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return

    # Load environment variables and validate API key
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found")
        print("Please create a .env file with: GEMINI_API_KEY=your-actual-api-key")
        return

    # Initialize the main extractor
    try:
        extractor = PDFMetadataExtractor(api_key)
        print("🔑 Gemini API connection established")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini API: {e}")
        print("Check your API key and internet connection")
        return

    # Process directory paths
    source_dir = os.path.abspath(args.source)
    output_dir = os.path.abspath(args.output)

    if not os.path.exists(source_dir):
        print(f"❌ Source directory {source_dir} does not exist")
        return

    # Display configuration and start processing
    print("🚀 Starting PDF metadata extraction...")
    print(f"📁 Source directory: {source_dir}")
    if not args.no_copy:
        print(f"📂 Output directory: {output_dir}")
    else:
        print("📄 Metadata extraction only (no file copying)")
    print(f"📄 Analyzing first {args.max_pages} pages of each PDF")

    # Determine results file location
    if args.no_copy:
        results_file_path = os.path.join(source_dir, DEFAULT_OUTPUT_FILE)
    else:
        results_file_path = os.path.join(output_dir, DEFAULT_OUTPUT_FILE)

    # Process all files in the directory
    results = extractor.process_directory(
        source_dir,
        output_dir if not args.no_copy else None,
        results_file_path,
        args.max_pages,
    )

    if not results:
        print("❌ No PDF files found or processed successfully")
        return

    # Display final results summary
    print("\n" + "=" * 80)
    print("📊 EXTRACTION RESULTS")
    print("=" * 80)

    # Count successes and display individual results
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
