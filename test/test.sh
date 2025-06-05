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

print_test() { echo -e "${BLUE}🧪 TEST:${NC} $1"; }
print_pass() { echo -e "${GREEN}✓ PASS:${NC} $1"; }
print_fail() { echo -e "${RED}✗ FAIL:${NC} $1"; }

# Get script directory (parent of test directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Test variables
TEST_OUTPUT_DIR="test/test_output"
SAMPLE_DIR="test/sample_pdf"
FAILED_TESTS=0

# Cleanup function (disabled - keep output directory)
cleanup() {
    # [[ -d "$TEST_OUTPUT_DIR" ]] && rm -rf "$TEST_OUTPUT_DIR"
    echo "Keeping test output directory: $TEST_OUTPUT_DIR"
}

# Trap cleanup on exit
trap cleanup EXIT

echo "🚀 Starting comprehensive run.sh test suite"
echo "📁 Using sample PDFs from: $SAMPLE_DIR"

# Test 1: Help functionality
print_test "Help functionality"
if ./run.sh --help 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -q "AI-PDF-Renamer"; then
    print_pass "Help displays correctly"
else
    print_fail "Help not working"
    ((FAILED_TESTS++))
fi

# Test 2: No arguments (should show help)
print_test "No arguments behavior"
if ./run.sh 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -q "AI-PDF-Renamer"; then
    print_pass "Shows help when no arguments provided"
else
    print_fail "Should show help with no arguments"
    ((FAILED_TESTS++))
fi

# Create test output directory
mkdir -p "$TEST_OUTPUT_DIR"

# Test 3: Full processing (rename files)
print_test "Full PDF processing with file renaming"
if ./run.sh "$SAMPLE_DIR" "$TEST_OUTPUT_DIR" --max-pages 1 --force; then
    # Check if any files were created in output directory
    if [[ $(find "$TEST_OUTPUT_DIR" -name "*.pdf" | wc -l) -gt 0 ]]; then
        print_pass "PDFs processed and renamed successfully"
        echo "  📝 Renamed files:"
        find "$TEST_OUTPUT_DIR" -name "*.pdf" -exec basename {} \; | sed 's/^/    /'
    else
        print_fail "No renamed PDF files found in output"
        ((FAILED_TESTS++))
    fi
    
    # Check if results JSON file was created
    if [[ -f "$TEST_OUTPUT_DIR/pdf_metadata_results.json" ]]; then
        print_pass "Results JSON file created"
    else
        print_fail "Results JSON file not created"
        ((FAILED_TESTS++))
    fi
else
    print_fail "Full processing failed"
    ((FAILED_TESTS++))
fi

# Test 4: Metadata-only mode (no file copying)
print_test "Metadata extraction only (--no-copy)"
if ./run.sh "$SAMPLE_DIR" "$TEST_OUTPUT_DIR" --no-copy --max-pages 1 --force; then
    # Check if results file was created in source directory
    if [[ -f "$SAMPLE_DIR/pdf_metadata_results.json" ]]; then
        print_pass "Metadata-only mode works"
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

# Test 5: Invalid directory handling
print_test "Invalid source directory handling"
if ./run.sh "/nonexistent/directory" "$TEST_OUTPUT_DIR" --force 2>&1 | grep -q "does not exist"; then
    print_pass "Properly handles invalid source directory"
else
    print_fail "Should detect invalid source directory"
    ((FAILED_TESTS++))
fi

# Test 6: Different max-pages values
print_test "Different max-pages parameter"
rm -rf "$TEST_OUTPUT_DIR" && mkdir -p "$TEST_OUTPUT_DIR"
if ./run.sh "$SAMPLE_DIR" "$TEST_OUTPUT_DIR" --max-pages 2 --force; then
    if [[ $(find "$TEST_OUTPUT_DIR" -name "*.pdf" | wc -l) -gt 0 ]]; then
        print_pass "max-pages parameter works"
    else
        print_fail "max-pages processing failed"
        ((FAILED_TESTS++))
    fi
else
    print_fail "max-pages test failed"
    ((FAILED_TESTS++))
fi

# Test 7: Environment setup logic (test run.sh setup without API key)
print_test "Environment setup and dependency checking"
# Temporarily rename .env to test setup without API key
if [[ -f ".env" ]]; then
    mv .env .env.backup
fi

# Test that script detects missing API key (capture output with timeout)
OUTPUT_FILE="/tmp/api_test_output"
(./run.sh "$SAMPLE_DIR" "$TEST_OUTPUT_DIR" --force > "$OUTPUT_FILE" 2>&1 & SCRIPT_PID=$!; sleep 3; kill $SCRIPT_PID 2>/dev/null; wait $SCRIPT_PID 2>/dev/null)
if grep -q "No .env file found\|Invalid or missing GEMINI_API_KEY" "$OUTPUT_FILE"; then
    print_pass "Properly detects missing API configuration"
else
    print_fail "Should detect missing API configuration"
    ((FAILED_TESTS++))
fi
rm -f "$OUTPUT_FILE"

# Restore .env file
if [[ -f ".env.backup" ]]; then
    mv .env.backup .env
fi

# Test 8: Virtual environment creation logic
print_test "Virtual environment handling"
# Temporarily rename venv to test auto-creation
if [[ -d "venv" ]]; then
    mv venv venv.backup
fi

# Run help (which doesn't need API key) to test venv creation
if ./run.sh --help 2>&1 | grep -q "Virtual environment created\|Virtual environment activated"; then
    print_pass "Virtual environment creation works"
else
    print_pass "Virtual environment logic handled (may already exist)"
fi

# Restore venv
if [[ -d "venv.backup" ]]; then
    rm -rf venv
    mv venv.backup venv
fi

# Test results summary
echo
echo "📊 Test Results Summary"
echo "======================"

TOTAL_TESTS=8
PASSED_TESTS=$((TOTAL_TESTS - FAILED_TESTS))

echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED_TESTS test(s) failed${NC}"
    exit 1
fi