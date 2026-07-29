import os
from pathlib import Path

OUTPUT_FILE = "repo_after_copilot_v4.txt"

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".pytest_cache",
    "dist",
    "build",
    ".mypy_cache"
}

ALLOWED_EXTENSIONS = {
    ".py",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".txt"
}


def write_separator(outfile, title):
    outfile.write("\n")
    outfile.write("=" * 120)
    outfile.write("\n")
    outfile.write(title)
    outfile.write("\n")
    outfile.write("=" * 120)
    outfile.write("\n\n")


def export_repository():
    root_dir = Path.cwd()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        write_separator(outfile, "REPOSITORY STRUCTURE")

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            level = len(Path(root).relative_to(root_dir).parts)
            indent = "    " * level

            outfile.write(f"{indent}{Path(root).name}/\n")

            sub_indent = "    " * (level + 1)

            for file in sorted(files):
                ext = Path(file).suffix.lower()
                if ext in ALLOWED_EXTENSIONS:
                    outfile.write(f"{sub_indent}{file}\n")

        outfile.write("\n\n")

        write_separator(outfile, "FILE CONTENTS")

        file_count = 0

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in sorted(files):
                path = Path(root) / file

                if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                    continue

                file_count += 1

                try:
                    size_kb = round(path.stat().st_size / 1024, 2)

                    write_separator(
                        outfile,
                        f"FILE: {path.relative_to(root_dir)} | SIZE: {size_kb} KB"
                    )

                    with open(path, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())

                    outfile.write("\n\n")

                except Exception as exc:
                    outfile.write(
                        f"[ERROR READING FILE: {path.relative_to(root_dir)}]\n"
                    )
                    outfile.write(f"{exc}\n\n")

        write_separator(outfile, "SUMMARY")
        outfile.write(f"Exported files: {file_count}\n")

    print(f"\nExport completed.")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    export_repository()