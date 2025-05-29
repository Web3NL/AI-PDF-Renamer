#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script to test PDF metadata extraction (requires valid API key)
"""

import os
from pdf_metadata_extractor import PDFMetadataExtractor

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables
    pass

from config import API_KEY_SETUP_INSTRUCTIONS, DEFAULT_SOURCE_DIR

def main():
    """
    Test PDF metadata extraction with live API calls.
    
    Validates API key setup, establishes connection to Gemini API,
    and processes PDFs in the source directory to verify functionality.
    """
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("\nTo get your API key:")
        for instruction in API_KEY_SETUP_INSTRUCTIONS:
            print(instruction)
        print("\nOnce you have your API key set, run:")
        print("   python3 pdf_metadata_extractor.py")
        return
    
    print("🔑 API key found! Testing PDF metadata extraction...")
    
    # Test with a simple example first
    try:
        extractor = PDFMetadataExtractor(api_key)
        print("✅ Gemini API connection established")
        
        # Process PDFs
        results = extractor.process_directory(DEFAULT_SOURCE_DIR)
        
        if results:
            print(f"\n📊 Successfully processed {len(results)} PDF files")
            for result in results:
                print(f"📄 {result.get('source_filename', 'Unknown file')}")
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
