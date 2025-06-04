#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive validation script for PDF Metadata Extractor setup.
Combines dependency checking, API validation, and basic functionality testing.
"""

import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from config import (
    API_KEY_SETUP_INSTRUCTIONS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCE_DIR,
    DEPENDENCY_INSTALL_INSTRUCTIONS,
)


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if all required packages are installed."""
    dependencies = [
        ("pdf2image", "pdf2image"),
        ("PIL", "Pillow"),
        ("google.generativeai", "google-generativeai"),
        ("dotenv", "python-dotenv"),
    ]

    missing = []
    for import_name, package_name in dependencies:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name}")
            missing.append(package_name)

    return len(missing) == 0


def check_system_dependencies():
    """Check if system-level dependencies are available."""
    # Check for poppler (required for pdf2image)
    import subprocess

    try:
        result = subprocess.run(["pdftoppm", "-h"], capture_output=True, text=True)
        print("✅ Poppler utilities (pdftoppm)")
        return True
    except FileNotFoundError:
        print("❌ Poppler utilities not found")
        print("   Install with: brew install poppler")
        return False


def check_api_key():
    """Check if API key is properly configured."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return False

    if len(api_key) < 20:  # Basic sanity check
        print("⚠️  GEMINI_API_KEY appears too short")
        return False

    print("✅ GEMINI_API_KEY configured")
    return True


def check_directory_structure():
    """Check if required directories exist."""
    src_dir = Path(DEFAULT_SOURCE_DIR)
    output_dir = Path(DEFAULT_OUTPUT_DIR)

    if not src_dir.exists():
        print(f"⚠️  Source directory {src_dir} doesn't exist")
        print(f"   Creating {src_dir}...")
        src_dir.mkdir(exist_ok=True)

    if not output_dir.exists():
        print(f"📁 Output directory {output_dir} will be created when needed")

    pdf_files = list(src_dir.glob("*.pdf")) + list(src_dir.glob("*.PDF"))
    print(f"📁 Source directory: {src_dir.absolute()}")
    print(f"📂 Output directory: {output_dir.absolute()}")
    print(f"📄 PDF files found: {len(pdf_files)}")

    return True


def run_basic_api_test():
    """Run a basic API connectivity test."""
    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return False

        genai.configure(api_key=api_key)
        # Just test configuration, don't make actual API calls
        print("✅ Gemini API configuration successful")
        return True
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False


def main():
    """Run comprehensive setup validation."""
    print("🔍 PDF Metadata Extractor - Comprehensive Setup Validation")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("Python Dependencies", check_dependencies),
        ("System Dependencies", check_system_dependencies),
        ("API Key Configuration", check_api_key),
        ("Directory Structure", check_directory_structure),
        ("API Connectivity", run_basic_api_test),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n🔄 Checking {name}...")
        result = check_func()
        results.append((name, result))

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {name}")
        if result:
            passed += 1

    print(f"\n📈 Results: {passed}/{len(results)} checks passed")

    if passed == len(results):
        print("\n🎉 All checks passed! You're ready to run the extractor:")
        print("   python3 pdf_metadata_extractor.py")
    else:
        print("\n🔧 Setup Issues Found:")
        if not results[1][1]:  # Dependencies failed
            print("\n📦 Install Python dependencies:")
            for instruction in DEPENDENCY_INSTALL_INSTRUCTIONS:
                print(f"   {instruction}")

        if not results[3][1]:  # API key failed
            print("\n🔑 Set up your API key:")
            for instruction in API_KEY_SETUP_INSTRUCTIONS:
                print(f"   {instruction}")


if __name__ == "__main__":
    main()
