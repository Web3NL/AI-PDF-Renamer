#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script to test PDF metadata extraction (requires valid API key)
"""

import json
import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from pdf_metadata_extractor import PDFMetadataExtractor

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables
    pass

from config import (
    API_KEY_SETUP_INSTRUCTIONS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_FILE,
    TEST_SOURCE_DIR,
)


def get_unique_output_filename(output_dir: str, base_filename: str) -> str:
    """Generate a unique filename in the output directory to avoid overwriting."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    base_path = output_path / base_filename
    if not base_path.exists():
        return str(base_path)

    # If file exists, add a number
    name_part = base_path.stem
    extension = base_path.suffix
    counter = 1

    while True:
        new_name = f"{name_part}_{counter}{extension}"
        new_path = output_path / new_name
        if not new_path.exists():
            return str(new_path)
        counter += 1


def main():
    """
    Test PDF metadata extraction with live API calls using sample PDFs.

    Validates API key setup, establishes connection to Gemini API,
    and processes PDFs in the sample_pdf directory to verify functionality.
    Creates renamed copies in the output directory and saves results there.
    """
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("\nTo get your API key:")
        for instruction in API_KEY_SETUP_INSTRUCTIONS:
            print(instruction)
        print("\nOnce you have your API key set, run:")
        print("   python3 pdf_metadata_extractor.py")
        return

    print("🔑 API key found! Testing PDF metadata extraction...")
    print(f"📁 Processing sample PDFs from: {TEST_SOURCE_DIR}")
    print(f"📂 Output directory: {DEFAULT_OUTPUT_DIR}")

    # Test with a simple example first
    try:
        extractor = PDFMetadataExtractor(api_key)
        print("✅ Gemini API connection established")

        # Process PDFs from sample_pdf directory
        results = extractor.process_directory(TEST_SOURCE_DIR, DEFAULT_OUTPUT_DIR)

        if results:
            print(f"\n📊 Successfully processed {len(results)} PDF files")
            for result in results:
                print(f"📄 {result.get('source_filename', 'Unknown file')}")

            # Save results to output directory with unique filename
            output_file = get_unique_output_filename(
                DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_FILE
            )
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {output_file}")
        else:
            print("❌ No PDFs found or processed")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nThis might be due to:")
        print("- Invalid API key")
        print("- Network connectivity issues")
        print("- API quota limits")


if __name__ == "__main__":
    main()
