#!/bin/bash

# PDF Metadata Extractor Runner Script
# This script runs the PDF metadata extractor with proper error handling

echo "🚀 Starting PDF Metadata Extractor..."
echo "📁 Working directory: $(pwd)"
echo "⏰ $(date)"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: python3 could not be found"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if the main script exists
if [ ! -f "src/pdf_metadata_extractor.py" ]; then
    echo "❌ ERROR: src/pdf_metadata_extractor.py not found"
    echo "Make sure you're running this script from the project root directory"
    exit 1
fi

# Check if data directory exists (default source directory)
if [ ! -d "data" ]; then
    echo "⚠️  Source directory 'data' not found"
    echo "Creating data directory for PDF files..."
    mkdir -p data
fi

# Count PDF files in data directory
pdf_count=$(find data -name "*.pdf" -o -name "*.PDF" | wc -l | tr -d ' ')
echo "🔍 Found $pdf_count PDF files in data directory"

if [ "$pdf_count" -eq 0 ]; then
    echo "⚠️  No PDF files found in data directory"
    echo "Please add PDF files to the data directory and try again"
    echo "Or specify a different source directory with:"
    echo "   python3 src/pdf_metadata_extractor.py /path/to/your/pdfs"
    exit 0
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found"
    echo "Make sure you have a .env file with your GEMINI_API_KEY"
    echo ""
fi

echo "▶️  Running PDF metadata extractor..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the Python script with data directory as default source
python3 src/pdf_metadata_extractor.py data

# Check the exit status
exit_status=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $exit_status -eq 0 ]; then
    echo "✅ PDF metadata extraction completed successfully!"
    echo "📄 Results saved to pdf_metadata_results.json"
    
    # Show summary if results file exists
    if [ -f "pdf_metadata_results.json" ]; then
        result_count=$(python3 -c "import json; data=json.load(open('pdf_metadata_results.json')); print(len(data))" 2>/dev/null || echo "?")
        echo "📊 Processed $result_count files"
    fi
else
    echo "❌ PDF metadata extraction failed with exit code $exit_status"
fi

echo "⏰ Completed at: $(date)"
