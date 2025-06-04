#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version information for AI-PDF-Renamer
"""

__version__ = "1.0.0"
__version_info__ = tuple(map(int, __version__.split(".")))

# Project metadata
PROJECT_NAME = "AI-PDF-Renamer"
PROJECT_DESCRIPTION = (
    "Automatically extract metadata from PDF files and rename them using AI"
)
PROJECT_URL = "https://github.com/Web3NL/AI-PDF-Renamer"
AUTHOR = "AI-PDF-Renamer Team"
LICENSE = "MIT"


def get_version():
    """Return the current version string."""
    return __version__


def get_version_info():
    """Return the current version as a tuple of integers."""
    return __version_info__


if __name__ == "__main__":
    print(f"{PROJECT_NAME} v{__version__}")
