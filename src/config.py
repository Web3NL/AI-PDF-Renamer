#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration constants for PDF Metadata Extractor
"""

# API Configuration
GEMINI_API_KEY_URL = "https://aistudio.google.com/app/apikey"
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Processing Configuration
DEFAULT_MAX_PAGES = 2  # Reduced from 3 - most metadata is on first 2 pages
DEFAULT_DPI = 200
DEFAULT_MAX_FILENAME_LENGTH = 100
DEFAULT_MAX_RETRIES = 3
DEFAULT_RATE_LIMIT_DELAY = 6  # seconds between API calls
DEFAULT_RETRY_BASE_DELAY = 60  # base delay for exponential backoff

# Directory Configuration (relative to project root)
DEFAULT_SOURCE_DIR = "./data"  # For actual user PDFs
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_OUTPUT_FILE = "pdf_metadata_results.json"
TEST_SOURCE_DIR = "./sample_pdf"

# File Extensions
PDF_EXTENSIONS = ["*.pdf", "*.PDF"]

# Messages
API_KEY_SETUP_INSTRUCTIONS = [
    f"1. Visit: {GEMINI_API_KEY_URL}",
    "2. Sign in with your Google account",
    "3. Click 'Create API Key'",
    "4. Copy the generated key",
    "5. Set it in your environment:",
    "   export GEMINI_API_KEY='your-actual-api-key'",
]

DEPENDENCY_INSTALL_INSTRUCTIONS = [
    "pip3 install -r requirements.txt",
    "brew install poppler",
]
