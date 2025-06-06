#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import namedtuple

__version__ = "2.1.0"
__version_info__ = namedtuple("VersionInfo", ["major", "minor", "patch"])(
    *map(int, __version__.split("."))
)

__title__ = "AI-PDF-Renamer"
__description__ = (
    "Automatically extract metadata from PDF files and rename them using AI"
)
__url__ = "https://github.com/Web3NL/AI-PDF-Renamer"
__author__ = "AI-PDF-Renamer Team"
__license__ = "MIT"


if __name__ == "__main__":
    print(f"{__title__} v{__version__}")
