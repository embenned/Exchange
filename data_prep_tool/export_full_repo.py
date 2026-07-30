from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TextIO

OUTPUT_FILE = "repo_full_export.txt"

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".idea", ".vscode",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox",
    "build", "dist", "logs", "node_modules", "site-packages",
}

IGNORE_FILES = {
    OUTPUT_FILE,
    "application.log",
    "Thumbs.db",
    ".DS_Store",
}

BINARY_EXTENSIONS = {
    ".xls", ".xlsx", ".xlsm", ".xlsb", ".xltx", ".xltm",
    ".doc", ".docx", ".ppt", ".pptx", ".pdf",
    ".zip", ".7z", ".rar", ".exe", ".dll", ".pyd", ".pyc",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp",
    ".tif", ".tiff", ".bin", ".db", ".sqlite", ".sqlite3",
}

SEPARATOR_LENGTH = 120


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
    except OSError as exc:
        return f"[Git command failed: {exc}]"

    parts: list[str] = []
    if result.stdout.strip():
        parts.append(result.stdout.rstrip())
    if result.stderr.strip():
        parts.extend(["[STDERR]", result.stderr.rstrip()])
    return "\n".join(parts) if parts else "[No output]"


def should_ignore_directory(directory_name: str) -> bool:
    return directory_name in IGNORE_DIRS


def should_ignore_file(path: Path) -> bool:
    if path.name in IGNORE_FILES:
        return True
    lowercase_name = path.name.lower()
    if lowercase_name.startswith("repo_after_") and path.suffix.lower() == ".txt":
        return True
    if lowercase_name.startswith("repo_full_export") and path.suffix.lower() == ".txt":
        return True
    return False


def collect_repository_files(root_dir: Path) -> list[Path]:
    collected_files: list[Path] = []

    for current_root, directories, files in os.walk(root_dir):
        directories[:] = sorted(
            directory
            for directory in directories
            if not should_ignore_directory(directory)
        )
        current_path = Path(current_root)

        for filename in sorted(files):
            file_path = current_path / filename
            if should_ignore_file(file_path):
                continue
            collected_files.append(file_path)

    return collected_files


def looks_binary(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    try:
        with path.open("rb") as infile:
            sample = infile.read(8192)
    except OSError:
        return True

    if not sample:
        return False
    if b"\x00" in sample:
        return True

    allowed_controls = {7, 8, 9, 10, 12, 13, 27}
    non_text_count = 0
    for byte in sample:
        ascii_printable = 32 <= byte <= 126
        allowed_control = byte in allowed_controls
        non_ascii = byte >= 128
        if not (ascii_printable or allowed_control or non_ascii):
            non_text_count += 1

    return non_text_count / len(sample) > 0.30


def read_text_file(path: Path) -> tuple[str | None, str]:
    encodings = ("utf-8-sig", "utf-8", "utf-16", "cp1250", "cp1252", "latin-1")
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            return None, f"read error: {exc}"
    return None, "unknown encoding"


def export_repository_information(
    outfile: TextIO,
    root_dir: Path,
    repository_files: list[Path],
) -> None:
    write_separator(outfile, "REPOSITORY EXPORT INFORMATION")
    outfile.write(f"Export date: {datetime.now().isoformat(timespec='seconds')}\n")
    outfile.write(f"Repository root: {root_dir}\n")
    outfile.write(f"Output file: {OUTPUT_FILE}\n")
    outfile.write(f"Discovered files: {len(repository_files)}\n")
    outfile.write(f"Ignored directories: {', '.join(sorted(IGNORE_DIRS))}\n")


def export_git_information(outfile: TextIO, root_dir: Path) -> None:
    write_separator(outfile, "GIT REPOSITORY INFORMATION")
    commands = [
        ("CURRENT COMMIT", ["rev-parse", "HEAD"]),
        ("CURRENT BRANCH", ["branch", "--show-current"]),
        ("GIT STATUS", ["status", "--short", "--untracked-files=all"]),
        ("TRACKED FILES", ["ls-files"]),
        ("LAST 10 COMMITS", ["log", "--oneline", "--decorate", "-10"]),
        ("UNCOMMITTED DIFF", ["diff", "--no-ext-diff"]),
        ("STAGED DIFF", ["diff", "--cached", "--no-ext-diff"]),
    ]
    for title, arguments in commands:
        outfile.write(f"{title}\n")
        outfile.write("-" * 40 + "\n")
        outfile.write(run_git_command(root_dir, arguments))
        outfile.write("\n\n")


def export_repository_structure(
    outfile: TextIO,
    root_dir: Path,
    repository_files: list[Path],
) -> None:
    write_separator(outfile, "REPOSITORY STRUCTURE")

    files_by_parent: dict[Path, list[Path]] = {}
    all_directories: set[Path] = {root_dir}

    for file_path in repository_files:
        files_by_parent.setdefault(file_path.parent, []).append(file_path)
        current_directory = file_path.parent
        while root_dir == current_directory or root_dir in current_directory.parents:
            all_directories.add(current_directory)
            if current_directory == root_dir:
                break
            current_directory = current_directory.parent

    sorted_directories = sorted(
        all_directories,
        key=lambda directory: (
            len(directory.relative_to(root_dir).parts),
            str(directory.relative_to(root_dir)).lower(),
        ),
    )

    for directory in sorted_directories:
        relative_directory = directory.relative_to(root_dir)
        if relative_directory == Path("."):
            level = 0
            display_name = f"{root_dir.name}/"
        else:
            level = len(relative_directory.parts)
            display_name = f"{directory.name}/"

        outfile.write(f"{'    ' * level}{display_name}\n")
        directory_files = sorted(
            files_by_parent.get(directory, []),
            key=lambda item: item.name.lower(),
        )
        for file_path in directory_files:
            try:
                size = file_path.stat().st_size
            except OSError:
                size = 0
            marker = "[BINARY]" if looks_binary(file_path) else "[TEXT]"
            outfile.write(
                f"{'    ' * (level + 1)}{marker} {file_path.name} ({format_size(size)})\n"
            )


def export_text_file_contents(
    outfile: TextIO,
    root_dir: Path,
    repository_files: list[Path],
) -> tuple[int, int]:
    write_separator(outfile, "TEXT FILE CONTENTS")
    exported_count = 0
    failed_count = 0

    for file_path in repository_files:
        if looks_binary(file_path):
            continue

        relative_path = file_path.relative_to(root_dir)
        try:
            size = file_path.stat().st_size
        except OSError:
            size = 0

        content, encoding = read_text_file(file_path)
        write_separator(
            outfile,
            f"FILE: {relative_path} | SIZE: {format_size(size)} | ENCODING: {encoding}",
        )

        if content is None:
            failed_count += 1
            outfile.write(f"[ERROR: Could not read text file: {relative_path}]\n")
            continue

        exported_count += 1
        outfile.write(content)
        if content and not content.endswith("\n"):
            outfile.write("\n")

    return exported_count, failed_count


def export_binary_inventory(
    outfile: TextIO,
    root_dir: Path,
    repository_files: list[Path],
) -> tuple[int, int]:
    write_separator(outfile, "BINARY FILE INVENTORY")
    binary_count = 0
    failed_hash_count = 0

    outfile.write("Binary file contents are not embedded in this text export.\n")
    outfile.write("Each binary file is listed with its path, size and SHA-256 hash.\n")
    outfile.write("Upload relevant Excel reports and workbooks separately.\n\n")

    for file_path in repository_files:
        if not looks_binary(file_path):
            continue

        binary_count += 1
        relative_path = file_path.relative_to(root_dir)
        try:
            size = file_path.stat().st_size
        except OSError:
            size = 0

        try:
            sha256 = calculate_sha256(file_path)
        except OSError as exc:
            sha256 = f"[HASH ERROR: {exc}]"
            failed_hash_count += 1

        outfile.write(f"Path: {relative_path}\n")
        outfile.write(f"Size: {format_size(size)} ({size} bytes)\n")
        outfile.write(f"SHA-256: {sha256}\n")
        outfile.write("-" * 80 + "\n")

    return binary_count, failed_hash_count


def export_summary(
    outfile: TextIO,
    repository_files: list[Path],
    text_count: int,
    text_failures: int,
    binary_count: int,
    binary_hash_failures: int,
) -> None:
    write_separator(outfile, "EXPORT SUMMARY")
    outfile.write(f"Total discovered files: {len(repository_files)}\n")
    outfile.write(f"Text files exported: {text_count}\n")
    outfile.write(f"Text read failures: {text_failures}\n")
    outfile.write(f"Binary files inventoried: {binary_count}\n")
    outfile.write(f"Binary hash failures: {binary_hash_failures}\n")
    success = text_failures == 0 and binary_hash_failures == 0
    outfile.write(f"Export status: {'SUCCESS' if success else 'COMPLETED WITH WARNINGS'}\n")


def export_repository() -> Path:
    root_dir = Path.cwd().resolve()
    output_path = root_dir / OUTPUT_FILE
    repository_files = collect_repository_files(root_dir)

    with output_path.open("w", encoding="utf-8", newline="\n") as outfile:
        export_repository_information(outfile, root_dir, repository_files)
        export_git_information(outfile, root_dir)
        export_repository_structure(outfile, root_dir, repository_files)
        text_count, text_failures = export_text_file_contents(
            outfile, root_dir, repository_files
        )
        binary_count, binary_hash_failures = export_binary_inventory(
            outfile, root_dir, repository_files
        )
        export_summary(
            outfile,
            repository_files,
            text_count,
            text_failures,
            binary_count,
            binary_hash_failures,
        )

    return output_path


if __name__ == "__main__":
    generated_file = export_repository()
    print()
    print("Repository export completed.")
    print(f"Output file: {generated_file}")
    print()
    print("Upload this text file for repository analysis.")
    print("Upload relevant .xlsx or .xlsm files separately.")
