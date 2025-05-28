#!/usr/bin/env python3
"""
Setup script to check dependencies and guide user through API setup
"""

import os
import sys

def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")
    
    try:
        import pdf2image
        print("✓ pdf2image installed")
    except ImportError:
        print("✗ pdf2image not installed")
        return False
    
    try:
        import PIL
        print("✓ Pillow installed")
    except ImportError:
        print("✗ Pillow not installed")
        return False
    
    try:
        import google.generativeai as genai
        print("✓ google-generativeai installed")
    except ImportError:
        print("✗ google-generativeai not installed")
        return False
    
    return True

def check_api_key():
    """Check if API key is set"""
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print("✓ GEMINI_API_KEY environment variable is set")
        return True
    else:
        print("✗ GEMINI_API_KEY environment variable not set")
        return False

def main():
    print("PDF Metadata Extractor Setup Check")
    print("=" * 40)
    
    deps_ok = check_dependencies()
    api_ok = check_api_key()
    
    if not deps_ok:
        print("\nTo install missing dependencies, run:")
        print("pip install -r requirements.txt")
        print("brew install poppler")
        return
    
    if not api_ok:
        print("\nTo set up your Gemini API key:")
        print("1. Visit: https://aistudio.google.com/app/apikey")
        print("2. Create a new API key")
        print("3. Set it as environment variable:")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        print("\nOr add it to your shell profile (.zshrc, .bashrc, etc.)")
        return
    
    print("\n✓ All dependencies and API key are set up correctly!")
    print("You can now run: python pdf_metadata_extractor.py")

if __name__ == "__main__":
    main()
