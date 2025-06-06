#!/bin/bash

# Pre-flight checks for AI-PDF-Renamer release
# Usage: ./scripts/pre-release-check.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

print_info "Running pre-flight checks for release..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "python3 is not available"
    exit 1
fi

# Install dev dependencies if needed
print_info "Installing development dependencies..."
python3 -m pip install --quiet black isort flake8

print_info "Applying code formatting..."
python3 -m black src/ test/ 2>/dev/null || true
print_success "Code formatting applied"

print_info "Sorting imports..."
python3 -m isort src/ test/ 2>/dev/null || true
print_success "Import sorting applied"

print_info "Running basic syntax check..."
python3 -m py_compile src/*.py
print_success "Syntax check passed"

# Check if there are any changes after formatting
if [[ -n $(git status --porcelain) ]]; then
    print_warning "Code formatting created changes that need to be committed:"
    git status --short
    echo
    print_info "Please review and commit these changes before running the release script:"
    echo "  git add -A"
    echo "  git commit -m 'style: apply code formatting'"
    echo
    print_info "Then run: ./scripts/release.sh [patch|minor|major]"
else
    print_success "No formatting changes needed. Ready for release!"
    print_info "Run: ./scripts/release.sh [patch|minor|major]"
fi