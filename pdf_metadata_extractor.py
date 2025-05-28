#!/usr/bin/env python3
"""
PDF Metadata Extractor using Google Gemini API
Extracts year of publication, author, and title from PDF documents
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
import base64
import io
import re
import shutil

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
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
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
        text = text.strip()[:100]
        return text
    
    def create_new_filename(self, metadata: Dict[str, Any]) -> str:
        """Create new filename from metadata in format: YEAR - AUTHOR - TITLE.pdf"""
        year = self.sanitize_filename(metadata.get('year', 'Unknown'))
        author = self.sanitize_filename(metadata.get('author', 'Unknown'))
        title = self.sanitize_filename(metadata.get('title', 'Unknown'))
        
        # Handle multiple authors - take first author if comma/and separated
        if ' and ' in author:
            author = author.split(' and ')[0].strip()
        elif ',' in author:
            author = author.split(',')[0].strip()
        
        # Create filename
        new_filename = f"{year} - {author} - {title}.pdf"
        return new_filename
    
    def rename_pdf_file(self, old_path: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Rename PDF file based on extracted metadata"""
        try:
            old_file = Path(old_path)
            directory = old_file.parent
            
            # Create new filename
            new_filename = self.create_new_filename(metadata)
            new_path = directory / new_filename
            
            # Avoid overwriting existing files
            counter = 1
            original_new_path = new_path
            while new_path.exists() and new_path != old_file:
                stem = original_new_path.stem
                new_path = directory / f"{stem} ({counter}).pdf"
                counter += 1
            
            # Rename the file
            if new_path != old_file:
                shutil.move(str(old_file), str(new_path))
                return {
                    "renamed": True,
                    "old_filename": old_file.name,
                    "new_filename": new_path.name,
                    "old_path": str(old_file),
                    "new_path": str(new_path)
                }
            else:
                return {
                    "renamed": False,
                    "reason": "Same filename",
                    "filename": old_file.name
                }
                
        except Exception as e:
            return {
                "renamed": False,
                "error": str(e),
                "old_filename": Path(old_path).name
            }
        
    def pdf_to_images(self, pdf_path: str, max_pages: int = 3) -> List[Image.Image]:
        """Convert PDF to images, focusing on first few pages"""
        try:
            # Convert first few pages to images (title page usually contains metadata)
            images = convert_from_path(pdf_path, first_page=1, last_page=max_pages, dpi=200)
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
    
    def extract_metadata_from_images(self, images: List[Image.Image], filename: str) -> Dict[str, Any]:
        """Extract metadata using Gemini API"""
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
        
        try:
            # Prepare image data for Gemini API
            image_parts = []
            for i, image in enumerate(images[:2]):  # Use first 2 pages maximum
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
            return {
                "error": f"API call failed: {str(e)}",
                "source_filename": filename
            }
    
    def process_pdf(self, pdf_path: str, rename_files: bool = True) -> Dict[str, Any]:
        """Process a single PDF file"""
        print(f"Processing: {pdf_path}")
        
        filename = os.path.basename(pdf_path)
        
        # Convert PDF to images
        images = self.pdf_to_images(pdf_path)
        if not images:
            return {
                "error": "Failed to convert PDF to images",
                "source_filename": filename
            }
        
        # Extract metadata
        metadata = self.extract_metadata_from_images(images, filename)
        
        # If extraction was successful and rename_files is True, rename the file
        if rename_files and 'error' not in metadata:
            rename_result = self.rename_pdf_file(pdf_path, metadata)
            metadata['rename_info'] = rename_result
            
            # Update source_filename if file was renamed
            if rename_result.get('renamed'):
                metadata['original_filename'] = filename
                metadata['source_filename'] = rename_result['new_filename']
                print(f"📝 Renamed: {filename} → {rename_result['new_filename']}")
        
        return metadata
    
    def process_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Process all PDF files in a directory"""
        results = []
        pdf_files = list(Path(directory_path).glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {directory_path}")
            return results
        
        for pdf_file in pdf_files:
            result = self.process_pdf(str(pdf_file))
            results.append(result)
        
        return results


def main():
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
        print("1. Visit: https://aistudio.google.com/app/apikey")
        print("2. Sign in with your Google account")
        print("3. Click 'Create API Key'")
        print("4. Copy the key and add it to your .env file")
        return
    
    # Initialize extractor
    try:
        extractor = PDFMetadataExtractor(api_key)
        print("🔑 Gemini API connection established")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini API: {e}")
        print("Check your API key and internet connection")
        return
    
    # Process PDFs in src directory
    src_dir = "./src"
    if not os.path.exists(src_dir):
        print(f"❌ Directory {src_dir} does not exist")
        return
    
    print("🚀 Starting PDF metadata extraction...")
    print(f"📁 Processing files in: {os.path.abspath(src_dir)}")
    
    results = extractor.process_directory(src_dir)
    
    if not results:
        print("❌ No PDF files found or processed successfully")
        return
    
    # Display results
    print("\n" + "="*80)
    print("📊 EXTRACTION RESULTS")
    print("="*80)
    
    successful_extractions = 0
    renamed_files = 0
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
            
            # Show rename information
            rename_info = result.get('rename_info', {})
            if rename_info.get('renamed'):
                renamed_files += 1
                print(f"📝 Renamed from: {rename_info['old_filename']}")
            elif 'error' in rename_info:
                print(f"⚠️  Rename failed: {rename_info['error']}")
            elif rename_info.get('reason') == 'Same filename':
                print(f"ℹ️  Filename unchanged (already correct format)")
    
    print(f"\n✅ Successfully processed {successful_extractions}/{len(results)} files")
    print(f"📝 Renamed {renamed_files} files")
    
    # Save results to JSON file
    output_file = "pdf_metadata_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: {output_file}")
    print("\n🎉 Processing complete!")


if __name__ == "__main__":
    main()
