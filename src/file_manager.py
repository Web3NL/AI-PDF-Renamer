#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict

from config import DEFAULT_MAX_FILENAME_LENGTH


class FileManager:
    """Handles file operations, naming, and results storage"""
    def update_results_file(
        self, results_file_path: str, new_result: Dict[str, Any]
    ) -> bool:
        """Append new extraction result to JSON results file"""
        try:
            # Create results directory if needed
            results_dir = os.path.dirname(results_file_path)
            if results_dir:
                os.makedirs(results_dir, exist_ok=True)

            # Load existing results or start fresh
            existing_results = []
            if os.path.exists(results_file_path):
                try:
                    with open(results_file_path, "r", encoding="utf-8") as f:
                        existing_results = json.load(f)
                    if not isinstance(existing_results, list):
                        existing_results = []
                except (json.JSONDecodeError, IOError):
                    existing_results = []

            existing_results.append(new_result)

            with open(results_file_path, "w", encoding="utf-8") as f:
                json.dump(existing_results, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"⚠️  Failed to update results file: {e}")
            return False

    def sanitize_filename(self, text: str) -> str:
        """Remove invalid characters from filename components"""
        if not text or text == "Not found":
            return "Unknown"

        # Remove filesystem-forbidden characters
        text = re.sub(r'[<>:"/\\|?*]', "", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text.replace("\n", " "))
        # Remove special symbols that cause issues
        text = re.sub(r"[†‡§¶#@$%^&*+={}[\]~`]", "", text)
        text = text.strip()[:DEFAULT_MAX_FILENAME_LENGTH]
        return text

    def _process_author_name(self, author_raw) -> str:
        """Extract first author from multi-author strings"""
        if isinstance(author_raw, list):
            author = str(author_raw[0]) if author_raw else "Unknown"
        else:
            author = str(author_raw)
        
        author = self.sanitize_filename(author)
        
        # Handle multiple authors - take first one
        if " and " in author.lower():
            author = author.split(" and ")[0].strip()
        elif " & " in author:
            author = author.split(" & ")[0].strip()
        elif ";" in author:
            author = author.split(";")[0].strip()
        # Handle comma-separated names (check for suffixes)
        elif author.count(",") > 1:
            parts = author.split(",")
            if len(parts) >= 2 and not any(suffix in parts[1].strip().lower() for suffix in ["jr", "sr", "ii", "iii", "iv"]):
                author = parts[0].strip()
            
        return author

    def create_new_filename(self, metadata: Dict[str, Any]) -> str:
        """Generate standardized filename: {year} - {author} - {title}.pdf"""
        year = self.sanitize_filename(metadata.get("year", "Unknown"))
        author = self._process_author_name(metadata.get("author", "Unknown"))
        title = self.sanitize_filename(metadata.get("title", "Unknown"))

        new_filename = f"{year} - {author} - {title}.pdf"
        return new_filename

    def copy_pdf_file(
        self, source_path: str, metadata: Dict[str, Any], output_dir: str
    ) -> Dict[str, str]:
        """Copy PDF to output directory with metadata-based filename"""
        try:
            source_file = Path(source_path)
            output_directory = Path(output_dir)

            # Create output directory if it doesn't exist
            output_directory.mkdir(exist_ok=True)

            # Generate new filename from metadata
            new_filename = self.create_new_filename(metadata)
            output_path = output_directory / new_filename

            # Handle filename conflicts with counter
            counter = 1
            base_stem = output_path.stem
            while output_path.exists():
                output_path = output_directory / f"{base_stem} ({counter}).pdf"
                counter += 1

            # Security check: ensure output path is within target directory
            resolved_output = output_path.resolve()
            resolved_output_dir = output_directory.resolve()
            try:
                resolved_output.relative_to(resolved_output_dir)
            except ValueError:
                raise ValueError(f"Output path {resolved_output} is outside target directory {resolved_output_dir}")

            shutil.copy2(str(source_file), str(output_path))
            return {
                "copied": True,
                "source_filename": source_file.name,
                "output_filename": output_path.name,
                "source_path": str(source_file),
                "output_path": str(output_path),
            }

        except Exception as e:
            return {
                "copied": False,
                "error": str(e),
                "source_filename": Path(source_path).name,
            }