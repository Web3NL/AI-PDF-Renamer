#!/bin/bash

# AI-PDF-Renamer - Main Entry Point
# Automatically extract metadata from PDF files and rename them using AI
# 
# This script handles environment setup and forwards all arguments to the Python application

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_header() { echo -e "${CYAN}🔍 $1${NC}"; }

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Show help if requested or no arguments provided
show_help() {
    print_header "AI-PDF-Renamer - Extract metadata and rename PDF files using AI"
    echo
    echo "USAGE:"
    echo "  $0 <source_dir> <output_dir> [options]"
    echo "  $0 --help"
    echo
    echo "ARGUMENTS:"
    echo "  source_dir          Directory containing PDF files to process"
    echo "  output_dir          Directory where renamed files will be saved"
    echo
    echo "OPTIONS:"
    echo "  --no-copy           Only extract metadata, don't copy/rename files"
    echo "  --max-pages N       Analyze only first N pages of each PDF (default: 2)"
    echo "  --model MODEL       AI model to use: flash (default) or pro"
    echo "  --force             Skip interactive confirmations (for automation)"
    echo "  --help              Show this help message"
    echo
    echo "EXAMPLES:"
    echo "  # Process PDFs and rename them:"
    echo "  $0 ./documents ./organized"
    echo
    echo "  # Only extract metadata (no file copying):"
    echo "  $0 ./documents ./results --no-copy"
    echo
    echo "  # Process only first page of each PDF:"
    echo "  $0 ./documents ./organized --max-pages 1"
    echo
    echo "  # Use Pro model for better accuracy:"
    echo "  $0 ./documents ./organized --model pro"
    echo
    echo "  # Batch processing for automation:"
    echo "  $0 ./documents ./organized --force"
    echo
    echo "SETUP REQUIREMENTS:"
    echo "  1. Get Google Gemini API key from: https://aistudio.google.com/app/apikey"
    echo "  2. Create .env file: echo 'GEMINI_API_KEY=your-key-here' > .env"
    echo "  3. Install system dependencies:"
    echo "     • macOS: brew install poppler"
    echo "     • Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo
    echo "For more information, see README.md"
}

# Check if help is requested or no arguments provided
if [[ $# -eq 0 ]] || [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
    exit 0
fi

print_header "AI-PDF-Renamer Starting..."

# Check if we're in the right directory
if [[ ! -f "src/main.py" ]]; then
    print_error "Cannot find src/main.py. Please run this script from the project root directory."
    exit 1
fi

# Check Python installation
print_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or later:"
    echo "  • macOS: brew install python3"
    echo "  • Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_success "Python $PYTHON_VERSION found"

# Check if virtual environment exists and activate it
if [[ -d "venv" ]]; then
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
else
    print_warning "No virtual environment found."
    print_info "Creating virtual environment for isolated dependencies..."
    if python3 -m venv venv; then
        source venv/bin/activate
        print_success "Virtual environment created and activated"
    else
        print_error "Failed to create virtual environment"
        print_info "You may need to install dependencies manually:"
        echo "pip3 install -r requirements.txt --user"
        exit 1
    fi
fi

# Check and install Python dependencies
print_info "Checking Python dependencies..."
MISSING_DEPS=()

# Check each required package
while IFS= read -r package; do
    # Skip empty lines and comments
    [[ -z "$package" || "$package" =~ ^#.*$ ]] && continue
    
    package_name=$(echo "$package" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1)
    
    if ! python3 -c "import $package_name" &> /dev/null; then
        # Special cases for package names that differ from import names
        case "$package_name" in
            "pdf2image") 
                if ! python3 -c "import pdf2image" &> /dev/null; then
                    MISSING_DEPS+=("$package")
                fi
                ;;
            "pillow")
                if ! python3 -c "import PIL" &> /dev/null; then
                    MISSING_DEPS+=("$package")
                fi
                ;;
            "google-generativeai")
                if ! python3 -c "import google.generativeai" &> /dev/null; then
                    MISSING_DEPS+=("$package")
                fi
                ;;
            "python-dotenv")
                if ! python3 -c "import dotenv" &> /dev/null; then
                    MISSING_DEPS+=("$package")
                fi
                ;;
            *)
                MISSING_DEPS+=("$package")
                ;;
        esac
    fi
done < requirements.txt

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    print_warning "Missing Python dependencies detected"
    echo "Installing: ${MISSING_DEPS[*]}"
    
    if ! pip3 install "${MISSING_DEPS[@]}"; then
        print_error "Failed to install dependencies. Please run manually:"
        echo "pip3 install -r requirements.txt"
        exit 1
    fi
    print_success "Dependencies installed successfully"
else
    print_success "All Python dependencies are installed"
fi

# Check for system dependencies (poppler for pdf2image)
print_info "Checking system dependencies..."
if ! command -v pdftoppm &> /dev/null; then
    print_error "poppler-utils not found (required for PDF processing)"
    echo "Please install poppler:"
    echo "  • macOS: brew install poppler"
    echo "  • Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "  • CentOS/RHEL: sudo yum install poppler-utils"
    exit 1
fi
print_success "System dependencies found"

# Check for .env file and API key
print_info "Checking API configuration..."
if [[ ! -f ".env" ]]; then
    print_error "No .env file found"
    echo "Please create a .env file with your Gemini API key:"
    echo "echo 'GEMINI_API_KEY=your-actual-api-key' > .env"
    echo
    echo "Get your API key from: https://aistudio.google.com/app/apikey"
    exit 1
fi

# Source .env and check if API key is set
if command -v python3 &> /dev/null; then
    API_KEY_CHECK=$(python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY', '')
if api_key and len(api_key.strip()) > 10:
    print('valid')
else:
    print('invalid')
" 2>/dev/null || echo "error")

    if [[ "$API_KEY_CHECK" == "valid" ]]; then
        print_success "Gemini API key configured"
    else
        print_error "Invalid or missing GEMINI_API_KEY in .env file"
        echo "Please ensure your .env file contains:"
        echo "GEMINI_API_KEY=your-actual-api-key"
        echo
        echo "Get your API key from: https://aistudio.google.com/app/apikey"
        exit 1
    fi
fi

print_success "Environment setup complete"
echo

# Forward all arguments to the Python script
print_info "Launching PDF metadata extractor..."
exec python3 src/main.py "$@"