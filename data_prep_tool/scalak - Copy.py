from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TextIO


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FILE = "repo_full_export.txt"

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "build",
    "dist",
    "logs",
    "node_modules",
    "site-packages",
}

IGNORE_FILES = {
    OUTPUT_FILE,
    "application.log",
    "Thumbs.db",
    ".DS_Store",
}

BINARY_EXTENSIONS = {
    ".xls",
    ".xlsx",
    ".xlsm",
    ".xlsb",
    ".xltx",
    ".xltm",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".pdf",
    ".zip",
    ".7z",
    ".rar",
    ".exe",
    ".dll",
    ".pyd",
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".bmp",
    ".tif",
    ".tiff",
    ".bin",
    ".db",
    ".sqlite",
    ".sqlite3",
}

SEPARATOR_LENGTH = 120


# ============================================================
# GENERAL HELPERS
# ============================================================

def write_separator(outfile: TextIO, title: str) -> None:
    outfile.write("\n")
    outfile.write("=" * SEPARATOR_LENGTH)
    outfile.write("\n")
    outfile.write(title)
    outfile.write("\n")
    outfile.write("=" * SEPARATOR_LENGTH)
    outfile.write("\n\n")


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"

    return f"{size_bytes / (1024 * 1024):.2f} MB"


def calculate_sha256(path: Path) -> str:
    hasher = hashlib.sha256()

    with path.open("rb") as infile:
        while True:
            chunk = infile.read(1024 * 1024)

            if not chunk:
                break

            hasher.update(chunk)

    return hasher.hexdigest()


def run_git_command(root_dir: Path, arguments: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return "[Git command is not available on this computer.]"
    except Exception as exc:
        return f"[Git command failed: {exc}]"

    output_parts: list[str] = []

    if result.stdout.strip():
        output_parts.append(result.stdout.rstrip())

    if result.stderr.strip():
        output_parts.append("[STDERR]")
        output_parts.append(result.stderr.rstrip())

    if not output_parts:
        return "[No output]"

    return "\n".join(output_parts)


# ============================================================
# FILE DISCOVERY
# ============================================================

def should_ignore_directory(directory_name: str) -> bool:
    return directory_name in IGNORE_DIRS


def should_ignore_file(path: Path) -> bool:
    if path.name in IGNORE_FILES:
        return True

    lowercase_name = path.name.lower()

    if lowercase_name.startswith("repo_after_") and path.