# AI-PDF-Renamer

🔍 **Automatically extract metadata from PDF files and rename them using AI**

This tool uses Google's Gemini AI to analyze PDF documents, extract key metadata (title, author, publication year), and automatically rename files in a standardized format for better organization.

## 🚀 Features

- **AI-Powered Extraction**: Uses Google Gemini AI to read PDF content and extract metadata
- **Smart Renaming**: Automatically renames files in format: `YEAR - AUTHOR - TITLE.pdf`
- **Batch Processing**: Process entire directories of PDF files at once
- **Non-Destructive**: Creates renamed copies while preserving original files
- **Rate Limiting**: Respects API limits with intelligent retry logic

## 📦 Installation

The `run.sh` script handles environment setup automatically, including virtual environment creation and dependency installation.

## 📖 Usage

```bash
# Setup: Get API key from https://aistudio.google.com/app/apikey
echo "GEMINI_API_KEY=your-actual-api-key-here" > .env

# Basic usage - process PDFs and rename them
./run.sh ./documents ./organized

# Extract metadata only (no file copying, saves JSON to source dir)
./run.sh ./documents ./results --no-copy

# Process only first page (faster/cheaper)
./run.sh ./documents ./organized --max-pages 1

# Automation mode (skip confirmations)
./run.sh ./documents ./organized --force

# Combine options
./run.sh ./papers ./organized --max-pages 1 --force
```

## 📊 Example Results

**Input**: `sample.pdf`  
**Output**: `2015 - André Koch Torres Assis - A new method for inductance calculation.pdf`

Results are also saved to `pdf_metadata_results.json` with detailed metadata for each processed file.
