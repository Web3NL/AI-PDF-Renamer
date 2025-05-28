# PDF Metadata Extractor

This tool uses Google's Gemini API to extract metadata (title, author, year) from PDF documents by converting them to images and analyzing them with AI.

## Quick Start

1. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Install Poppler (required for PDF to image conversion):**
   ```bash
   brew install poppler
   ```

3. **Get a Gemini API key:**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Sign in with your Google account
   - Click "Create API Key" 
   - Copy the generated key
   - Set it as an environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

4. **Test your setup:**
   ```bash
   python3 setup_check.py
   ```

5. **Run the extractor:**
   ```bash
   python3 pdf_metadata_extractor.py
   ```

The script will:
- Process all PDF files in the `src/` directory
- Convert the first few pages to images
- Use Gemini API to analyze the images and extract metadata
- Display results in the terminal
- Save results to `pdf_metadata_results.json`

## Current PDFs to Process

Your `src/` folder contains:
- `Assis - A new method for inductance.pdf`
- `Assis - Circuit theory in Weber electrodynamic.pdf` 
- `Koen van Vlaenderen - GCED 04-12-2015.pdf`

## Features

- **Automatic PDF Processing**: Converts PDFs to images for AI analysis
- **Smart Metadata Extraction**: Uses Gemini's vision capabilities to identify titles, authors, and publication years
- **Batch Processing**: Handles multiple PDFs in one run
- **JSON Output**: Saves structured results for further processing
- **Error Handling**: Gracefully handles conversion and API errors

## Output Format

The tool outputs metadata in this format:
```json
{
  "title": "Full title of the paper",
  "author": "Author name(s)",
  "year": "Publication year",
  "source_filename": "original_pdf_name.pdf"
}
```

## Limitations

- Requires internet connection for Gemini API calls
- PDF text must be clear and readable in image format
- Works best with standard academic paper formats
- API usage costs may apply for large volumes
