#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration constants for PDF Metadata Extractor
"""

# API Configuration
GEMINI_API_KEY_URL = "https://aistudio.google.com/app/apikey"
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Processing Configuration
DEFAULT_MAX_PAGES = 3
DEFAULT_DPI = 200
DEFAULT_MAX_FILENAME_LENGTH = 100
DEFAULT_MAX_RETRIES = 3
DEFAULT_RATE_LIMIT_DELAY = 6  # seconds between API calls
DEFAULT_RETRY_BASE_DELAY = 60  # base delay for exponential backoff

# Directory Configuration
DEFAULT_SOURCE_DIR = "./src"
DEFAULT_OUTPUT_FILE = "pdf_metadata_results.json"

# File Extensions
PDF_EXTENSIONS = ["*.pdf", "*.PDF"]

# Messages
API_KEY_SETUP_INSTRUCTIONS = [
    f"1. Visit: {GEMINI_API_KEY_URL}",
    "2. Sign in with your Google account",
    "3. Click 'Create API Key'",
    "4. Copy the generated key",
    "5. Set it in your environment:",
    "   export GEMINI_API_KEY='your-actual-api-key'"
]

DEPENDENCY_INSTALL_INSTRUCTIONS = [
    "pip3 install -r requirements.txt",
    "brew install poppler"
]
