#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Gemini API model version for metadata extraction
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"

# PDF processing defaults
DEFAULT_MAX_PAGES = 2  # Pages to analyze per PDF (cost optimization)
DEFAULT_DPI = 200  # Image resolution for PDF conversion
DEFAULT_MAX_FILENAME_LENGTH = 100  # Max chars in generated filenames
DEFAULT_MAX_RETRIES = 3  # API retry attempts on failure
DEFAULT_RATE_LIMIT_DELAY = 6  # Seconds between API calls (Gemini rate limit)
DEFAULT_RETRY_BASE_DELAY = 60  # Base delay for exponential backoff

# File paths and extensions
DEFAULT_OUTPUT_FILE = "pdf_metadata_results.json"  # Results filename
TEST_SOURCE_DIR = "./sample_pdf"  # Default test directory
PDF_EXTENSIONS = ["*.pdf", "*.PDF"]  # Supported file extensions


