#!/bin/bash

# Release script for AI-PDF-Renamer
# Usage: ./scripts/release.sh [patch|minor|major]

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

# Check if working directory is clean
if [[ -n $(git status --porcelain) ]]; then
    print_error "Working directory is not clean. Please commit or stash changes first."
    git status --short
    exit 1
fi

# Check if we're on the main branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "master" && "$CURRENT_BRANCH" != "main" ]]; then
    print_warning "You're not on the main branch (current: $CURRENT_BRANCH)"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Aborted"
        exit 0
    fi
fi

# Get current version from git tags (source of truth)
print_info "Fetching latest tags from remote..."
git fetch --tags

# Get the latest tag by version number (not just reachable from current commit)
LATEST_TAG=$(git tag -l | grep '^v[0-9]' | sort -V | tail -1)
if [[ -z "$LATEST_TAG" ]]; then
    LATEST_TAG="v0.0.0"
fi
CURRENT_VERSION=${LATEST_TAG#v}  # Remove 'v' prefix
print_info "Latest git tag: $LATEST_TAG"
print_info "Current version: $CURRENT_VERSION"

# Verify version.py is in sync (and update if needed)
VERSION_PY_VERSION=$(grep '^__version__ = ' src/version.py | sed 's/__version__ = "\(.*\)"/\1/')
if [[ "$VERSION_PY_VERSION" != "$CURRENT_VERSION" ]]; then
    print_warning "version.py ($VERSION_PY_VERSION) is out of sync with latest tag ($CURRENT_VERSION)"
    print_info "Updating version.py to match latest tag..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^__version__ = \".*\"/__version__ = \"$CURRENT_VERSION\"/" src/version.py
    else
        sed -i "s/^__version__ = \".*\"/__version__ = \"$CURRENT_VERSION\"/" src/version.py
    fi
    print_success "version.py updated to $CURRENT_VERSION"
fi

# Parse version components
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Determine new version
VERSION_TYPE="${1:-patch}"
case $VERSION_TYPE in
    patch)
        NEW_PATCH=$((PATCH + 1))
        NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"
        ;;
    minor)
        NEW_MINOR=$((MINOR + 1))
        NEW_VERSION="$MAJOR.$NEW_MINOR.0"
        ;;
    major)
        NEW_MAJOR=$((MAJOR + 1))
        NEW_VERSION="$NEW_MAJOR.0.0"
        ;;
    *)
        print_error "Invalid version type. Use: patch, minor, or major"
        exit 1
        ;;
esac

print_info "New version will be: $NEW_VERSION"

# Confirm the release
echo
print_warning "This will:"
echo "  1. Run pre-flight checks (formatting, syntax check)"
echo "  2. Update src/version.py to version $NEW_VERSION"
echo "  3. Commit the version bump"
echo "  4. Create and push tag v$NEW_VERSION"
echo "  5. Trigger the GitHub Actions release workflow"
echo

read -p "Continue with release? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Release aborted"
    exit 0
fi

# Store the current commit for potential rollback
ORIGINAL_COMMIT=$(git rev-parse HEAD)

# Function to rollback on failure
rollback() {
    print_warning "Rolling back changes..."
    git reset --hard "$ORIGINAL_COMMIT"
    git tag -d "v$NEW_VERSION" 2>/dev/null || true
    print_error "Release failed and changes have been rolled back"
    exit 1
}

# Set trap for cleanup on failure
trap rollback ERR

print_info "Starting release process..."

# 1. Pre-flight checks
print_info "Running pre-flight checks..."

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

# 2. Update version in version.py
print_info "Updating version in src/version.py..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/version.py
else
    # Linux
    sed -i "s/^__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/version.py
fi

# Also update the version_info tuple
NEW_VERSION_TUPLE=$(echo "$NEW_VERSION" | sed 's/\./", "/g')
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^__version_info__ = tuple.*/__version_info__ = tuple(map(int, __version__.split('.')))/" src/version.py
else
    # Linux
    sed -i "s/^__version_info__ = tuple.*/__version_info__ = tuple(map(int, __version__.split('.')))/" src/version.py
fi

# 3. Verify the version was updated correctly
UPDATED_VERSION=$(grep '^__version__ = ' src/version.py | sed 's/__version__ = "\(.*\)"/\1/')
if [[ "$UPDATED_VERSION" != "$NEW_VERSION" ]]; then
    print_error "Failed to update version in src/version.py"
    exit 1
fi
print_success "Version updated to $NEW_VERSION"

# 4. Commit the changes
print_info "Committing version bump..."
git add src/version.py
git commit -m "chore: bump version to $NEW_VERSION

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 5. Create and push tag
print_info "Creating tag v$NEW_VERSION..."
git tag "v$NEW_VERSION"

print_info "Pushing commit and tag..."
git push origin "$CURRENT_BRANCH"
git push origin "v$NEW_VERSION"

# Remove the error trap since we succeeded
trap - ERR

print_success "Release v$NEW_VERSION completed successfully!"
print_info "GitHub Actions will now build and publish the release."
print_info "Monitor progress at: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"

# Show the release URL
REPO_URL=$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')
print_info "Release will be available at: https://github.com/$REPO_URL/releases/tag/v$NEW_VERSION"
