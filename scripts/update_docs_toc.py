#!/usr/bin/env python3
"""
update_docs_toc.py — Re-index docs/ and update docs/toc.json.

Scans the docs/ directory for .md and .html files, extracts titles and
descriptions, and writes an updated toc.json. This script is called by
the /update-docs Claude Code skill and can also be run standalone.

Usage:
    python3 scripts/update_docs_toc.py [--docs-dir docs] [--output docs/toc.json]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def extract_md_title(filepath: Path) -> tuple[str, str]:
    """Extract title (first H1) and first paragraph from a Markdown file."""
    title = filepath.stem
    description = ""
    lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()

    for i, line in enumerate(lines):
        stripped = line.strip()
        # First H1 heading
        if stripped.startswith("# ") and title == filepath.stem:
            title = stripped.lstrip("# ").strip()
        # First non-empty, non-heading line after title = description
        elif title != filepath.stem and stripped and not stripped.startswith("#"):
            # Strip markdown formatting for a clean description
            description = re.sub(r"[>\*_`\[\]\(\)]", "", stripped).strip()
            break

    return title, description


def extract_html_title(filepath: Path) -> tuple[str, str]:
    """Extract <title> and first <meta name='description'> from an HTML file."""
    content = filepath.read_text(encoding="utf-8", errors="replace")

    title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else filepath.stem

    desc_match = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
        content,
        re.IGNORECASE,
    )
    description = desc_match.group(1).strip() if desc_match else ""

    return title, description


# Directories inside docs/ that are managed separately and excluded from the TOC.
EXCLUDED_DIRS = {"journal"}


def scan_docs(docs_dir: Path) -> list[dict]:
    """Scan docs directory and return file metadata.

    Skips directories listed in EXCLUDED_DIRS (e.g. journal/).
    """
    entries = []

    for filepath in sorted(docs_dir.rglob("*")):
        if not filepath.is_file():
            continue
        if filepath.suffix.lower() not in (".md", ".html"):
            continue
        # Skip excluded subdirectories (e.g. docs/journal/)
        rel_to_docs = filepath.relative_to(docs_dir)
        if rel_to_docs.parts and rel_to_docs.parts[0] in EXCLUDED_DIRS:
            continue

        rel_path = str(filepath.relative_to(docs_dir.parent))
        stat = filepath.stat()

        if filepath.suffix.lower() == ".md":
            title, description = extract_md_title(filepath)
        else:
            title, description = extract_html_title(filepath)

        entries.append(
            {
                "path": rel_path,
                "title": title,
                "description": description,
                "type": filepath.suffix.lstrip(".").lower(),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
            }
        )

    return entries


def update_toc_json(docs_dir: Path, output_path: Path) -> dict:
    """Scan docs and write toc.json. Returns the TOC data."""
    files = scan_docs(docs_dir)

    toc = {
        "generated": datetime.now(tz=timezone.utc).isoformat(),
        "repo": "brainvat/c64u-bbs",
        "files": files,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(toc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    return toc


def main():
    parser = argparse.ArgumentParser(description="Update docs/toc.json index")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Path to docs directory (default: docs)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/toc.json"),
        help="Output path for toc.json (default: docs/toc.json)",
    )
    args = parser.parse_args()

    if not args.docs_dir.is_dir():
        print(f"Error: {args.docs_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    toc = update_toc_json(args.docs_dir, args.output)
    print(f"Updated {args.output} with {len(toc['files'])} entries:")
    for entry in toc["files"]:
        print(f"  {entry['path']} — {entry['title']}")


if __name__ == "__main__":
    main()
