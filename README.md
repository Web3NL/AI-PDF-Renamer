# AI-PDF-Renamer

🔍 **Automatically extract metadata from PDF files and rename them using AI**

This tool uses Google's Gemini AI to analyze PDF documents, extract key metadata (title, author, publication year), and automatically rename files in a standardized format for better organization.

## 🚀 Features

- **AI-Powered Extraction**: Uses Google Gemini Vision AI to read PDF content and extract metadata
- **Smart Renaming**: Automatically renames files in format: `YEAR - AUTHOR - TITLE.pdf`
- **Batch Processing**: Process entire directories of PDF files at once
- **Non-Destructive**: Creates renamed copies while preserving original files
- **Comprehensive Setup**: Built-in validation and setup assistance
- **Rate Limiting**: Respects API limits with intelligent retry logic
- **Cross-Platform**: Works on macOS, Linux, and Windows

## 📋 Quick Start

### 1. Install Dependencies

```bash
# Install Python packages
pip3 install -r requirements.txt

# Install system dependencies (macOS)
brew install poppler

# For Ubuntu/Debian:
# sudo apt-get install poppler-utils
```

### 2. Get API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

### 3. Set Up Environment

```bash
# Set your API key
export GEMINI_API_KEY='your-actual-api-key-here'

# Or create a .env file:
echo "GEMINI_API_KEY=your-actual-api-key-here" > .env
```

### 4. Run the Tool

```bash
# Process PDFs in current directory
python3 src/pdf_metadata_extractor.py

# Process specific directory
python3 src/pdf_metadata_extractor.py /path/to/your/pdfs

# Advanced options
python3 src/pdf_metadata_extractor.py --source ./documents --output ./organized
```

## 📁 Project Structure

```
├── src/
│   ├── pdf_metadata_extractor.py  # Main extraction tool
│   └── config.py                  # Configuration settings
├── tests/
│   ├── validate_setup.py          # Comprehensive setup validation
│   ├── setup_check.py             # Basic dependency check
│   └── test_demo.py               # Live demo with sample PDFs
├── examples/
│   └── demo_results.py            # Sample output demonstration
├── sample_pdf/                    # Sample PDFs for testing
├── scripts/
│   └── run.sh                     # Shell script runner
├── output/                        # Generated renamed files
└── requirements.txt               # Python dependencies
```

## 🧪 Testing & Validation

The project includes comprehensive testing tools:

```bash
# Full setup validation (recommended)
python3 tests/validate_setup.py

# Basic dependency check
python3 tests/setup_check.py

# Live demo with sample PDFs
python3 tests/test_demo.py

# Show sample results format
python3 examples/demo_results.py
```

## 📊 Example Results

**Input**: `sample.pdf`
**Output**: `2015 - André Koch Torres Assis - A new method for inductance calculation.pdf`

**JSON Results**:
```json
{
  "title": "A new method for inductance calculation",
  "author": "André Koch Torres Assis",
  "year": "2015",
  "source_filename": "sample.pdf",
  "output_filename": "2015 - André Koch Torres Assis - A new method for inductance calculation.pdf"
}
```

## ⚙️ Command Line Options

```bash
python3 src/pdf_metadata_extractor.py [SOURCE_DIR] [OPTIONS]

Positional Arguments:
  SOURCE_DIR              Source directory with PDF files (default: current directory)

Options:
  --output, -o DIR        Output directory for renamed files (default: ./output)
  --results, -r FILE      Results JSON filename (default: pdf_metadata_results.json)
  --max-pages, -p NUM     Maximum pages to analyze per PDF (default: 2)
  --no-copy              Only extract metadata, don't copy files
  -h, --help             Show help message

Examples:
  python3 src/pdf_metadata_extractor.py
  python3 src/pdf_metadata_extractor.py /path/to/pdfs
  python3 src/pdf_metadata_extractor.py --source ./docs --output ./organized
  python3 src/pdf_metadata_extractor.py --max-pages 1    # Faster, analyze only first page
  python3 src/pdf_metadata_extractor.py --max-pages 5    # More thorough, analyze first 5 pages
  python3 src/pdf_metadata_extractor.py --no-copy        # metadata only
```

## 🔧 Configuration

Key settings in `src/config.py`:

- **Rate Limiting**: 6 seconds between API calls (respects Gemini limits)
- **Image Quality**: 200 DPI for optimal OCR accuracy
- **Page Limit**: Analyzes first 2 pages by default (configurable with --max-pages)
- **Retry Logic**: 3 attempts with exponential backoff for rate limits
- **Filename Sanitization**: Removes invalid characters, limits length

**Page Analysis Options**:
- `--max-pages 1`: Fastest, only title page (good for simple papers)
- `--max-pages 2`: Default, covers most metadata locations
- `--max-pages 3-5`: More thorough for complex documents with scattered metadata
- Higher values: Slower and more expensive, rarely needed

## 🔍 How It Works

1. **PDF Conversion**: Converts PDF pages to high-quality images using pdf2image
2. **AI Analysis**: Sends images to Google Gemini Vision AI for content analysis
3. **Metadata Extraction**: AI identifies and extracts title, author, and publication year
4. **Filename Generation**: Creates standardized filename from extracted metadata
5. **File Management**: Copies files to output directory with new names
6. **Results Storage**: Saves detailed extraction results in JSON format

## 🛠️ Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
- Ensure you've set the environment variable or created a .env file
- Verify the API key is valid and has proper permissions

**"pdf2image conversion failed"**
- Install poppler-utils: `brew install poppler` (macOS) or `sudo apt-get install poppler-utils` (Ubuntu)

**"Rate limit exceeded"**
- The tool automatically handles rate limits with retries
- For heavy usage, consider upgrading your Google AI API quota

**"Permission denied"**
- Ensure you have read access to source PDFs and write access to output directory

### Getting Help

1. Run the validation script: `python3 tests/validate_setup.py`
2. Check the detailed error messages in the console output
3. Verify all dependencies are properly installed
4. Ensure your API key is valid and has sufficient quota

## 📝 License

This project is open source. Feel free to use, modify, and distribute.

## 🙏 Acknowledgments

- **Google Gemini AI** - For powerful document analysis capabilities
- **pdf2image** - For reliable PDF to image conversion
- **Pillow** - For image processing and manipulation

---

**Happy organizing!** 📚✨

For questions or support, please check the troubleshooting section or run the built-in validation tools.
