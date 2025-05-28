#!/usr/bin/env python3
"""
Sample output demonstration - shows what results will look like
"""

import json
from datetime import datetime

def show_sample_results():
    """Show what the extraction results would look like"""
    
    print("🔍 PDF METADATA EXTRACTION - SAMPLE RESULTS")
    print("=" * 60)
    print("This is what your results will look like once you set up your API key:\n")
    
    # Sample results based on the PDF filenames
    sample_results = [
        {
            "title": "A new method for inductance calculation",
            "author": "André Koch Torres Assis",
            "year": "2015",
            "source_filename": "Assis - A new method for inductance.pdf"
        },
        {
            "title": "Circuit theory in Weber electrodynamics",
            "author": "André Koch Torres Assis",
            "year": "2014", 
            "source_filename": "Assis - Circuit theory in Weber electrodynamic.pdf"
        },
        {
            "title": "General Classical Electrodynamics",
            "author": "Koen van Vlaenderen",
            "year": "2015",
            "source_filename": "Koen van Vlaenderen - GCED 04-12-2015.pdf"
        }
    ]
    
    # Display sample results
    for i, result in enumerate(sample_results, 1):
        print(f"{i}. 📄 File: {result['source_filename']}")
        print("-" * 50)
        print(f"📖 Title:  {result['title']}")
        print(f"👤 Author: {result['author']}")
        print(f"📅 Year:   {result['year']}")
        print()
    
    print("💾 Results will be saved to: pdf_metadata_results.json")
    print("📊 Format: JSON with title, author, year, and source filename")
    
    # Show JSON structure
    print("\n📋 Sample JSON output:")
    print(json.dumps(sample_results[0], indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 60)
    print("🚀 TO GET STARTED:")
    print("1. Get your Gemini API key from: https://aistudio.google.com/app/apikey")
    print("2. Set it: export GEMINI_API_KEY='your-key'")
    print("3. Run: python3 pdf_metadata_extractor.py")

if __name__ == "__main__":
    show_sample_results()
