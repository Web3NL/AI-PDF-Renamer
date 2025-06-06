# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-PDF-Renamer is a Python CLI tool that uses Google Gemini AI to extract metadata (title, author, year) from PDF files and automatically rename them in a standardized format: `YEAR - AUTHOR - TITLE.pdf`.

## Core Architecture

The application follows a modular design with clear separation of concerns:

- **main.py**: Entry point and orchestration. Contains `PDFMetadataExtractor` class that coordinates all processing
- **pdf_processor.py**: Converts PDF pages to images using pdf2image/poppler
- **metadata_extractor.py**: Handles Gemini AI API calls with retry logic and rate limiting
- **file_manager.py**: Manages file operations, filename sanitization, and JSON results storage
- **config.py**: Central configuration constants (API model, rate limits, defaults)

## Common Commands

### Running the Application
```bash
# Main entry point (handles environment setup automatically)
./run.sh <source_dir> <output_dir> [options]

# Examples
./run.sh ./documents ./organized --max-pages 1 --force
./run.sh ./papers ./results --no-copy  # metadata only, no file copying
```

### Testing
```bash
# Run comprehensive test suite
./test/test.sh

# Tests require .env file with GEMINI_API_KEY for full functionality
```

### Development Setup
```bash
# Virtual environment is auto-created by run.sh, but manual setup:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# System dependency (required for pdf2image)
brew install poppler  # macOS
sudo apt-get install poppler-utils  # Ubuntu/Debian
```

### Release Management
```bash
# Create new release (updates version.py, creates git tag)
./scripts/release.sh [patch|minor|major]

# Applies code formatting and runs pre-flight checks automatically
```

## Key Implementation Details

### Rate Limiting and API Management
- Uses 6-second delays between Gemini API calls (configurable in `config.py`)
- Implements exponential backoff for rate limit errors (60s base delay)
- Retry logic handles transient errors (timeouts, network issues)
- API model version specified in `config.py` (currently gemini-2.5-flash-preview-05-20)

### PDF Processing Pipeline
1. `PDFProcessor.pdf_to_images()` converts first N pages to PIL Images
2. `MetadataExtractor.extract_metadata_from_images()` sends to Gemini API
3. `FileManager.copy_pdf_file()` creates renamed copy if requested

### Error Handling Patterns
- All modules return standardized error dictionaries with "error" key
- Graceful degradation: continues processing remaining files on individual failures
- Incremental JSON results saving prevents data loss on interruption

### File Naming and Sanitization
- Standardized format: `{year} - {author} - {title}.pdf`
- Robust filename sanitization removes filesystem-forbidden characters
- Automatic conflict resolution with numbered suffixes
- Multi-author handling (extracts first author only)

## Configuration Notes

- Environment variable `GEMINI_API_KEY` required (loaded via python-dotenv)
- Default processing: first 2 pages per PDF (cost optimization)
- Results saved to `pdf_metadata_results.json` in output directory
- Maximum filename length: 100 characters (truncated if longer)