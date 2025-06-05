# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Setup and Dependencies
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install system dependencies (macOS)
brew install poppler

# Install development dependencies for linting/formatting
python3 -m pip install black isort flake8
```

### Testing and Validation
```bash
# Comprehensive setup validation (recommended)
python3 tests/validate_setup.py

# Basic dependency check
python3 tests/setup_check.py

# Live demo with sample PDFs (requires API key)
python3 tests/test_demo.py

# Show sample results format
python3 examples/demo_results.py
```

### Code Quality
```bash
# Format code
python3 -m black src/ tests/ examples/

# Sort imports
python3 -m isort src/ tests/ examples/

# Basic syntax check
python3 -m py_compile src/pdf_metadata_extractor.py src/version.py
```

### Running the Application
```bash
# Run with default settings (processes data/ directory)
python3 src/pdf_metadata_extractor.py

# Run with shell script wrapper
./scripts/run.sh

# Process specific directory
python3 src/pdf_metadata_extractor.py /path/to/pdfs

# With custom options
python3 src/pdf_metadata_extractor.py --source ./docs --output ./organized --max-pages 3
```

### Release Management
```bash
# Create new release (patch/minor/major)
./scripts/release.sh patch
./scripts/release.sh minor
./scripts/release.sh major
```

## Architecture Overview

### Core Components
- **`src/pdf_metadata_extractor.py`**: Main application with PDFMetadataExtractor class that handles PDF-to-image conversion, AI analysis via Google Gemini, and file management
- **`src/config.py`**: Centralized configuration including API settings, rate limits, file paths, and default values
- **`src/version.py`**: Version management with semantic versioning support

### Data Flow
1. **PDF Processing**: Uses pdf2image with poppler to convert PDF pages to high-DPI images
2. **AI Analysis**: Sends images to Google Gemini Vision API to extract title, author, and publication year
3. **File Management**: Generates standardized filenames and copies files to output directory
4. **Results Storage**: Maintains JSON results file with extraction metadata

### Key Design Patterns
- **Rate Limiting**: Built-in 6-second delays and exponential backoff for API compliance
- **Error Recovery**: Comprehensive retry logic with graceful degradation
- **Incremental Processing**: Updates JSON results file after each successful extraction
- **Non-Destructive**: Always preserves original files while creating renamed copies

### Configuration System
All settings centralized in `src/config.py`:
- API configuration (model, rate limits, retries)
- Processing defaults (DPI, page limits, filename length)
- Directory structure and file extensions
- User-friendly error messages and setup instructions

### Testing Strategy
- **Validation Scripts**: Comprehensive environment and dependency checking
- **Demo Testing**: Live API testing with sample PDFs
- **Setup Verification**: Multi-layered validation before processing

## Environment Requirements

### Required Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key (get from https://aistudio.google.com/app/apikey)

### Required System Dependencies
- Python 3.8+
- poppler-utils (for PDF processing)
- All Python packages from requirements.txt

### Directory Structure
- `data/`: Default input directory for user PDFs
- `sample_pdf/`: Sample PDFs for testing
- `output/`: Default output directory for renamed files
- Results stored as `pdf_metadata_results.json` in project root