#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script to check dependencies and guide user through API setup
"""

import os
import sys

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables
    pass

from config import API_KEY_SETUP_INSTRUCTIONS, DEPENDENCY_INSTALL_INSTRUCTIONS


def check_dependencies():
    """
    Check if required packages are installed.

    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    print("Checking dependencies...")

    try:
        import pdf2image

        print("✅ pdf2image installed")
    except ImportError:
        print("❌ pdf2image not installed")
        return False

    try:
        import PIL

        print("✅ Pillow installed")
    except ImportError:
        print("❌ Pillow not installed")
        return False

    try:
        import google.generativeai as genai

        print("✅ google-generativeai installed")
    except ImportError:
        print("❌ google-generativeai not installed")
        return False

    return True


def check_api_key():
    """
    Check if API key is set in environment.

    Returns:
        bool: True if GEMINI_API_KEY is set, False otherwise
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("✅ GEMINI_API_KEY environment variable is set")
        return True
    else:
        print("❌ GEMINI_API_KEY environment variable not set")
        return False


def main():
    """
    Main setup validation function.

    Performs comprehensive checks of dependencies and API configuration,
    providing user guidance for any missing requirements.
    """
    print("PDF Metadata Extractor Setup Check")
    print("=" * 40)

    deps_ok = check_dependencies()
    api_ok = check_api_key()

    if not deps_ok:
        print("\nTo install missing dependencies, run:")
        for instruction in DEPENDENCY_INSTALL_INSTRUCTIONS:
            print(instruction)
        return

    if not api_ok:
        print("\nTo set up your Gemini API key:")
        for instruction in API_KEY_SETUP_INSTRUCTIONS:
            print(instruction)
        print("\nOr add it to your shell profile (.zshrc, .bashrc, etc.)")
        return

    print("\n✅ All dependencies and API key are set up correctly!")
    print("You can now run: python3 pdf_metadata_extractor.py")


if __name__ == "__main__":
    main()
