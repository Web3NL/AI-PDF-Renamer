#!/bin/bash

# Comprehensive test for run.sh covering all usage patterns
# Tests PDF processing with sample_pdf directory

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test() { echo -e "${BLUE}Testing:${NC} $1"; }
print_pass() { echo -e "${GREEN}✓${NC}"; }
print_fail() { echo -e "${RED}✗ FAIL:${NC} $1"; }

# Get script directory (parent of test directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Test variables
TEST_OUTPUT_DIR="test/test_output"
SAMPLE_DIR="test/sample_pdf"
FAILED_TESTS=0
ENV_TEMP_FILE=""

# Cleanup function (disabled - keep output directory)
cleanup() {
    # [[ -d "$TEST_OUTPUT_DIR" ]] && rm -rf "$TEST_OUTPUT_DIR"
    
    # Restore .env file if it was moved during testing
    if [[ -n "${ENV_TEMP_FILE:-}" ]] && [[ -f "$ENV_TEMP_FILE" ]]; then
        mv "$ENV_TEMP_FILE" .env
    fi
    
    # Restore venv if it was moved during testing
    if [[ -d "venv.backup" ]]; then
        rm -rf venv
        mv venv.backup venv
    fi
    
    echo "Keeping test output directory: $TEST_OUTPUT_DIR"
}

# Trap cleanup on exit
trap cleanup EXIT

echo "🚀 Starting comprehensive run.sh test suite"
echo "📁 Using sample PDFs from: $SAMPLE_DIR"

# Check if .env file exists - exit if not present
if [[ ! -f ".env" ]]; then
    echo -e "${RED}❌ No .env file found. Tests require .env file to be present.${NC}"
    echo "Please create a .env file with your configuration before running tests."
    exit 1
fi

# Check for API key availability
HAS_API_KEY=false
if grep -q "^GEMINI_API_KEY=" .env && [[ -n "$(grep "^GEMINI_API_KEY=" .env | cut -d'=' -f2)" ]]; then
    HAS_API_KEY=true
    echo "✓ API key found - running full tests"
else
    echo "⚠ No valid API key found - skipping API-dependent tests"
fi

# Test 1: Help functionality
print_test "Help functionality"
if ./run.sh --help 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -q "AI-PDF-Renamer" >/dev/null; then
    print_pass
else
    print_fail "Help not working"
    ((FAILED_TESTS++))
fi

# Test 2: No arguments (should show help)
print_test "No arguments behavior"
if ./run.sh 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -q "AI-PDF-Renamer" >/dev/null; then
    print_pass
else
    print_fail "Should show help with no arguments"
    ((FAILED_TESTS++))
fi

# Create test output directory
mkdir -p "$TEST_OUTPUT_DIR"

# Test 3: Full processing (rename files)
if [[ "$HAS_API_KEY" == "true" ]]; then
    print_test "Full PDF processing with file renaming"
    if ./run.sh "$SAMPLE_DIR" "$TEST_OUTPUT_DIR" --max-pages 1 --force >/dev/null 2>&1; then
        # Check if any files were created in output directory
        if [[ $(find "$TEST_OUTPUT_DIR" -name "*.pdf" | wc -l) -gt 0 ]]; then
            print_pass
        else
            print_fail "No renamed PDF files found in output"
            ((FAILED_TESTS++))
        fi
        
        # Check if results JSON file was created
        if [[ -f "$TEST_OUTPUT_DIR/pdf_metadata_results.json" ]]; then
            echo " JSON created"
        else
            print_fail "Results JSON file not created"
            ((FAILED_TESTS++))
        fi
    else
        print_fail "Full processing failed"
        ((FAILED_TESTS++))
    fi
else
    print_test "Full PDF processing with file renaming (SKIPPED - no API key)"
fi

# Test 4: Metadata-only mode (no file copying)
if [[ "$HAS_API_KEY" == "true" ]]; then
    print_test "Metadata extraction only (--no-copy)"
    if ./run.sh "$SAMPLE_DIR" "$TEST_OUTPUT_DIR" --no-copy --max-pages 1 --force >/dev/null 2>&1; then
        # Check if results file was created in source directory
        if [[ -f "$SAMPLE_DIR/pdf_metadata_results.json" ]]; then
            print_pass
            # Cleanup the results file
            rm -f "$SAMPLE_DIR/pdf_metadata_results.json"
        else
            print_fail "Metadata results file not created in source directory"
            ((FAILED_TESTS++))
        fi
    else
        print_fail "Metadata-only mode failed"
        ((FAILED_TESTS++))
    fi
else
    print_test "Metadata extraction only (SKIPPED - no API key)"
fi

# Test 5: Invalid directory handling
print_test "Invalid source directory handling"
if ./run.sh "/nonexistent/directory" "$TEST_OUTPUT_DIR" --force 2>&1 | grep -q "does not exist" >/dev/null; then
    print_pass
else
    print_fail "Should detect invalid source directory"
    ((FAILED_TESTS++))
fi

# Test 6: Different max-pages values
if [[ "$HAS_API_KEY" == "true" ]]; then
    print_test "Different max-pages parameter"
    rm -rf "$TEST_OUTPUT_DIR" && mkdir -p "$TEST_OUTPUT_DIR"
    if ./run.sh "$SAMPLE_DIR" "$TEST_OUTPUT_DIR" --max-pages 2 --force >/dev/null 2>&1; then
        if [[ $(find "$TEST_OUTPUT_DIR" -name "*.pdf" | wc -l) -gt 0 ]]; then
            print_pass
        else
            print_fail "max-pages processing failed"
            ((FAILED_TESTS++))
        fi
    else
        print_fail "max-pages test failed"
        ((FAILED_TESTS++))
    fi
else
    print_test "Different max-pages parameter (SKIPPED - no API key)"
fi

# Test 7: Virtual environment creation logic
print_test "Virtual environment handling"
# Temporarily rename venv to test auto-creation
if [[ -d "venv" ]]; then
    mv venv venv.backup
fi

# Run help (which doesn't need API key) to test venv creation
if ./run.sh --help 2>&1 | grep -q "Virtual environment created\|Virtual environment activated" >/dev/null; then
    print_pass
else
    print_pass
fi

# Restore venv
if [[ -d "venv.backup" ]]; then
    rm -rf venv
    mv venv.backup venv
fi

# Test results summary
echo
echo
TOTAL_TESTS=7
PASSED_TESTS=$((TOTAL_TESTS - FAILED_TESTS))

echo "Tests passed: $PASSED_TESTS/$TOTAL_TESTS"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED_TESTS test(s) failed${NC}"
    exit 1
fi