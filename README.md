# AI-PDF-Renamer

🔍 **Automatically extract metadata from PDF files and rename them using AI**

This tool uses Google's Gemini AI to analyze PDF documents, extract key metadata (title, author, publication year), and automatically rename files in a standardized format for better organization.

## 🚀 Features

- **AI-Powered Extraction**: Uses Google Gemini Vision AI to read PDF content and extract metadata
- **Smart Renaming**: Automatically renames files in format: `YEAR - AUTHOR - TITLE.pdf`
- **Batch Processing**: Process entire directories of PDF files at once
- **Non-Destructive**: Creates renamed copies while preserving original files
- **Rate Limiting**: Respects API limits with intelligent retry logic
- **Cross-Platform**: Works on macOS, Linux, and Windows

## 📋 Quick Start



# Create a .env file:
echo "GEMINI_API_KEY=your-actual-api-key-here" > .env
```

### 4. Run the Tool

### 📊 Example Results

**Input**: `sample.pdf`
**Output**: `2015 - André Koch Torres Assis - A new method for inductance calculation.pdf`


