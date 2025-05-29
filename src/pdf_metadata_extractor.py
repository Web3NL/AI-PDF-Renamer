#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Metadata Extractor using Google Gemini API
Extracts year of publication, author, and title from PDF documents
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import base64
import io
import re
import shutil
import time
from datetime import datetime

# Import configuration constants
from config import (
    DEFAULT_MAX_PAGES, DEFAULT_DPI, DEFAULT_MAX_FILENAME_LENGTH,
    DEFAULT_MAX_RETRIES, DEFAULT_RATE_LIMIT_DELAY, DEFAULT_RETRY_BASE_DELAY,
    GEMINI_MODEL, DEFAULT_SOURCE_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_FILE,
    API_KEY_SETUP_INSTRUCTIONS
)

try:
    from pdf2image import convert_from_path
    from PIL import Image
    import google.generativeai as genai
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required packages. Please install them:")
    print("pip3 install pdf2image pillow google-generativeai python-dotenv")
    print("Also install poppler-utils: brew install poppler")
    exit(1)


class PDFMetadataExtractor:
    def __init__(self, api_key: str):
        """Initialize the extractor with Gemini API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def update_results_file(self, results_file_path: str, new_result: Dict[str, Any]) -> bool:
        """Safely update the JSON results file with a new result"""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(results_file_path), exist_ok=True)
            
            # Read existing results or create new list
            existing_results = []
            if os.path.exists(results_file_path):
                try:
                    with open(results_file_path, 'r', encoding='utf-8') as f:
                        existing_results = json.load(f)
                    if not isinstance(existing_results, list):
                        existing_results = []
                except (json.JSONDecodeError, IOError):
                    # If file is corrupted or unreadable, start fresh
                    existing_results = []
            
            # Add the new result
            existing_results.append(new_result)
            
            # Write back to file
            with open(results_file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_results, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"⚠️  Failed to update results file: {e}")
            return False
    
    def sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filename"""
        if not text or text == "Not found":
            return "Unknown"
        
        # Remove or replace invalid filename characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace newlines and excessive whitespace
        text = re.sub(r'\s+', ' ', text.replace('\n', ' '))
        # Remove special characters that might cause issues
        text = re.sub(r'[†‡§¶#@$%^&*+={}[\]~`]', '', text)
        # Limit length to avoid filesystem issues
        text = text.strip()[:DEFAULT_MAX_FILENAME_LENGTH]
        return text
    
    def create_new_filename(self, metadata: Dict[str, Any]) -> str:
        """Create new filename from metadata in format: YEAR - AUTHOR - TITLE.pdf"""
        year = self.sanitize_filename(metadata.get('year', 'Unknown'))
        
        # Handle author field - it might be a string or a list
        author_raw = metadata.get('author', 'Unknown')
        if isinstance(author_raw, list):
            # If it's a list, take the first author and convert to string
            author = str(author_raw[0]) if author_raw else 'Unknown'
        else:
            author = str(author_raw)
        
        author = self.sanitize_filename(author)
        title = self.sanitize_filename(metadata.get('title', 'Unknown'))
        
        # Handle multiple authors - take first author if comma/and separated
        if ' and ' in author:
            author = author.split(' and ')[0].strip()
        elif ',' in author:
            author = author.split(',')[0].strip()
        
        # Create filename
        new_filename = f"{year} - {author} - {title}.pdf"
        return new_filename
    
    def copy_pdf_file(self, source_path: str, metadata: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """Copy PDF file to output directory with new name based on extracted metadata"""
        try:
            source_file = Path(source_path)
            output_directory = Path(output_dir)
            
            # Create output directory if it doesn't exist
            output_directory.mkdir(exist_ok=True)
            
            # Create new filename
            new_filename = self.create_new_filename(metadata)
            output_path = output_directory / new_filename
            
            # Avoid overwriting existing files in output directory
            counter = 1
            original_output_path = output_path
            while output_path.exists():
                stem = original_output_path.stem
                output_path = output_directory / f"{stem} ({counter}).pdf"
                counter += 1
            
            # Copy the file to output directory
            shutil.copy2(str(source_file), str(output_path))
            return {
                "copied": True,
                "source_filename": source_file.name,
                "output_filename": output_path.name,
                "source_path": str(source_file),
                "output_path": str(output_path)
            }
                
        except Exception as e:
            return {
                "copied": False,
                "error": str(e),
                "source_filename": Path(source_path).name
            }
        
    def pdf_to_images(self, pdf_path: str, max_pages: int = DEFAULT_MAX_PAGES) -> List[Image.Image]:
        """Convert PDF to images, focusing on first few pages"""
        try:
            # Convert first few pages to images (title page usually contains metadata)
            images = convert_from_path(pdf_path, first_page=1, last_page=max_pages, dpi=DEFAULT_DPI)
            return images
        except Exception as e:
            print(f"Error converting PDF {pdf_path}: {e}")
            return []
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode()
    
    def extract_metadata_from_images(self, images: List[Image.Image], filename: str, max_pages: int = None) -> Dict[str, Any]:
        """Extract metadata using Gemini API with retry logic for rate limits"""
        if not images:
            return {"error": "No images to process"}
        
        # Prepare the prompt for metadata extraction
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
        base_delay = DEFAULT_RETRY_BASE_DELAY  # Base delay for rate limiting (60 seconds)
        
        for attempt in range(max_retries):
            try:
                # Prepare image data for Gemini API
                image_parts = []
                # Use all available images up to max_pages, with fallback to 2
                max_images = max_pages if max_pages is not None else min(len(images), 2)
                for i, image in enumerate(images[:max_images]):
                    image_parts.append({
                        "mime_type": "image/png",
                        "data": self.image_to_base64(image)
                    })
                
                # Create the content with images and prompt
                content = image_parts + [prompt]
                
                # Generate response
                response = self.model.generate_content(content)
                
                # Parse JSON response
                try:
                    response_text = response.text.strip()
                    
                    # Remove markdown code blocks if present
                    if response_text.startswith('```json'):
                        response_text = response_text[7:]  # Remove ```json
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]  # Remove ```
                    
                    response_text = response_text.strip()
                    
                    result = json.loads(response_text)
                    result["source_filename"] = filename
                    return result
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, try to extract info from text response
                    return {
                        "title": "Could not parse JSON response",
                        "author": "Could not parse JSON response", 
                        "year": "Could not parse JSON response",
                        "source_filename": filename,
                        "raw_response": response.text,
                        "parse_error": str(e)
                    }
                    
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Calculate delay with exponential backoff
                        delay = base_delay * (2 ** attempt)
                        print(f"⏳ Rate limit hit for {filename}. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(delay)
                        continue
                    else:
                        return {
                            "error": f"Rate limit exceeded after {max_retries} attempts: {error_str}",
                            "source_filename": filename
                        }
                else:
                    # For other errors, don't retry
                    return {
                        "error": f"API call failed: {error_str}",
                        "source_filename": filename
                    }
        
        return {
            "error": f"Failed after {max_retries} attempts",
            "source_filename": filename
        }
    
    def process_pdf(self, pdf_path: str, output_dir: str = None, copy_files: bool = True, max_pages: int = DEFAULT_MAX_PAGES) -> Dict[str, Any]:
        """Process a single PDF file"""
        print(f"Processing: {pdf_path}")
        
        filename = os.path.basename(pdf_path)
        
        # Convert PDF to images
        images = self.pdf_to_images(pdf_path, max_pages)
        if not images:
            return {
                "error": "Failed to convert PDF to images",
                "source_filename": filename
            }
        
        # Extract metadata
        metadata = self.extract_metadata_from_images(images, filename, max_pages)
        
        # If extraction was successful and copy_files is True, copy the file
        if copy_files and output_dir and 'error' not in metadata:
            copy_result = self.copy_pdf_file(pdf_path, metadata, output_dir)
            metadata['copy_info'] = copy_result
            
            # Update source_filename to show the output filename
            if copy_result.get('copied'):
                metadata['output_filename'] = copy_result['output_filename']
                print(f"📝 Copied: {filename} → {copy_result['output_filename']}")
        
        return metadata
    
    def process_directory(self, directory_path: str, output_dir: str = DEFAULT_OUTPUT_DIR, results_file_path: str = None, max_pages: int = DEFAULT_MAX_PAGES) -> List[Dict[str, Any]]:
        """Process all PDF files in a directory with rate limiting and incremental results saving"""
        results = []
        directory = Path(directory_path)
        pdf_files = list(directory.glob("*.pdf")) + list(directory.glob("*.PDF"))
        
        if not pdf_files:
            print(f"No PDF files found in {directory_path}")
            return results
        
        print(f"🔍 Found {len(pdf_files)} PDF files to process")
        if output_dir:
            print(f"📁 Output directory: {os.path.abspath(output_dir)}")
        else:
            print("📄 Metadata extraction only (no file copying)")
        
        if results_file_path:
            print(f"💾 Results will be saved incrementally to: {os.path.abspath(results_file_path)}")
        
        print(f"⏰ Rate limiting: {DEFAULT_RATE_LIMIT_DELAY} seconds between API calls to respect Gemini's rate limits")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n🔄 Processing file {i}/{len(pdf_files)} at {datetime.now().strftime('%H:%M:%S')}")
            
            # Determine if we should copy files based on whether output_dir is provided
            copy_files = output_dir is not None
            result = self.process_pdf(str(pdf_file), output_dir, copy_files, max_pages)
            results.append(result)
            
            # Save result incrementally to JSON file if specified
            if results_file_path:
                if self.update_results_file(results_file_path, result):
                    print(f"📝 Result saved to {os.path.basename(results_file_path)}")
                else:
                    print(f"⚠️  Failed to save result for {result.get('source_filename', 'unknown file')}")
            
            # Add delay between API calls to respect rate limits (except for last file)
            if i < len(pdf_files):
                if 'error' not in result:  # Only delay if we successfully made an API call
                    print(f"⏳ Waiting {DEFAULT_RATE_LIMIT_DELAY} seconds to respect API rate limits...")
                    time.sleep(DEFAULT_RATE_LIMIT_DELAY)
        
        return results


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract metadata from PDF files using Google Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 pdf_metadata_extractor.py                     # Process PDFs in current directory
  python3 pdf_metadata_extractor.py /path/to/pdfs      # Process PDFs in specified directory
  python3 pdf_metadata_extractor.py --source ./docs --output ./results
  python3 pdf_metadata_extractor.py --max-pages 1      # Only analyze first page (faster)
  python3 pdf_metadata_extractor.py --max-pages 5      # Analyze first 5 pages (slower but more thorough)
  cd /my/pdf/folder && python3 /path/to/pdf_metadata_extractor.py
        """
    )
    
    parser.add_argument(
        'source',
        nargs='?',
        default='.',
        help='Source directory containing PDF files (default: current directory)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default=DEFAULT_OUTPUT_DIR,
        help=f'Output directory for renamed files (default: {DEFAULT_OUTPUT_DIR})'
    )
    
    parser.add_argument(
        '--results', '-r',
        default=DEFAULT_OUTPUT_FILE,
        help=f'Results JSON filename (default: {DEFAULT_OUTPUT_FILE})'
    )
    
    parser.add_argument(
        '--no-copy',
        action='store_true',
        help='Only extract metadata, do not copy files'
    )
    
    parser.add_argument(
        '--max-pages', '-p',
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f'Maximum number of pages to analyze per PDF (default: {DEFAULT_MAX_PAGES})'
    )
    
    return parser.parse_args()


def main():
    """
    Main execution function for PDF metadata extraction.
    
    Coordinates the entire extraction process including:
    - Command-line argument parsing
    - Environment setup and API key validation
    - PDF processing and metadata extraction
    - File copying to output directory and result storage
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Validate max_pages argument
    if args.max_pages < 1:
        print("❌ ERROR: --max-pages must be at least 1")
        return
    if args.max_pages > 10:
        print("⚠️  WARNING: --max-pages > 10 may be slow and expensive for API costs")
        try:
            confirm = input("Continue anyway? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("Operation cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found")
        print("\n📋 Please check your .env file:")
        print("1. Make sure you have a .env file in this directory")
        print("2. It should contain: GEMINI_API_KEY=your-actual-api-key")
        print("\n💡 If you don't have an API key yet:")
        for instruction in API_KEY_SETUP_INSTRUCTIONS:
            print(instruction)
        return
    
    # Initialize extractor
    try:
        extractor = PDFMetadataExtractor(api_key)
        print("🔑 Gemini API connection established")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini API: {e}")
        print("Check your API key and internet connection")
        return
    
    # Resolve paths
    source_dir = os.path.abspath(args.source)
    output_dir = os.path.abspath(args.output)
    
    # Check if source directory exists
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
    
    # Prepare results file path if specified
    results_file_path = None
    if args.results:
        # Always save results in output directory to keep source directory clean
        # Even with --no-copy, we still create output directory for results
        results_file_path = os.path.join(output_dir, args.results)
    
    results = extractor.process_directory(source_dir, output_dir if not args.no_copy else None, results_file_path, args.max_pages)
    
    if not results:
        print("❌ No PDF files found or processed successfully")
        return
    
    # Display results
    print("\n" + "="*80)
    print("📊 EXTRACTION RESULTS")
    print("="*80)
    
    successful_extractions = 0
    copied_files = 0
    for i, result in enumerate(results, 1):
        print(f"\n{i}. 📄 File: {result.get('source_filename', 'Unknown')}")
        print("-" * 60)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            successful_extractions += 1
            print(f"📖 Title:  {result.get('title', 'Not found')}")
            print(f"👤 Author: {result.get('author', 'Not found')}")
            print(f"📅 Year:   {result.get('year', 'Not found')}")
            
            # Show copy information
            if not args.no_copy:
                copy_info = result.get('copy_info', {})
                if copy_info.get('copied'):
                    copied_files += 1
                    print(f"📝 Copied to: {copy_info['output_filename']}")
                elif 'error' in copy_info:
                    print(f"⚠️  Copy failed: {copy_info['error']}")
    
    print(f"\n✅ Successfully processed {successful_extractions}/{len(results)} files")
    if not args.no_copy:
        print(f"📝 Copied {copied_files} files to output directory")
    
    # Results are now saved incrementally during processing
    if args.results and results_file_path:
        print(f"💾 All results saved incrementally to: {results_file_path}")
    
    print("\n🎉 Processing complete!")


if __name__ == "__main__":
    main()
