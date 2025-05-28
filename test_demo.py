#!/usr/bin/env python3
"""
Demo script to test PDF metadata extraction (requires valid API key)
"""

import os
from pdf_metadata_extractor import PDFMetadataExtractor

def main():
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("\nTo get your API key:")
        print("1. Visit: https://aistudio.google.com/app/apikey")
        print("2. Sign in with your Google account")
        print("3. Click 'Create API Key'")
        print("4. Copy the generated key")
        print("5. Set it in your environment:")
        print("   export GEMINI_API_KEY='your-actual-api-key'")
        print("\nOnce you have your API key set, run:")
        print("   python3 pdf_metadata_extractor.py")
        return
    
    print("🔑 API key found! Testing PDF metadata extraction...")
    
    # Test with a simple example first
    try:
        extractor = PDFMetadataExtractor(api_key)
        print("✅ Gemini API connection established")
        
        # Process PDFs
        results = extractor.process_directory("./src")
        
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
