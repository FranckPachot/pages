#!/usr/bin/env python3
"""Install the site's Google tag in existing and generated HTML pages."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


MEASUREMENT_ID = "G-LFQ153SCQM"
GOOGLE_TAG = f'''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{MEASUREMENT_ID}');
</script>'''
HEAD_PATTERN = re.compile(r"(<head\b[^>]*>)[ \t]*", re.IGNORECASE)
PLACEMENT_PATTERN = re.compile(r"<head\b[^>]*>\s*<!-- Google tag \(gtag\.js\) -->", re.IGNORECASE)


def add_google_tag(document: str) -> str:
    """Return HTML with exactly one site tag inserted after the opening head."""
    if MEASUREMENT_ID in document:
        return document
    updated, count = HEAD_PATTERN.subn(rf"\1\n{GOOGLE_TAG}", document, count=1)
    return updated if count else document


def install_google_tag(path: Path) -> bool:
    try:
        document = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    updated = add_google_tag(document)
    if updated == document:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def install_google_tags(root: Path) -> tuple[int, int]:
    candidates = sorted({*root.rglob("*.html"), *root.rglob("*.htm")})
    changed = sum(install_google_tag(path) for path in candidates)
    tagged = 0
    for path in candidates:
        try:
            tagged += MEASUREMENT_ID in path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return changed, tagged


def audit_google_tags(root: Path) -> tuple[int, list[Path], list[Path], list[Path]]:
    pages_with_head = 0
    missing = []
    misplaced = []
    duplicated = []
    for path in sorted({*root.rglob("*.html"), *root.rglob("*.htm")}):
        try:
            document = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not HEAD_PATTERN.search(document):
            continue
        pages_with_head += 1
        marker_count = document.count("<!-- Google tag (gtag.js) -->")
        if marker_count == 0 or MEASUREMENT_ID not in document:
            missing.append(path)
        if marker_count > 1:
            duplicated.append(path)
        if marker_count and not PLACEMENT_PATTERN.search(document):
            misplaced.append(path)
    return pages_with_head, missing, misplaced, duplicated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--check", action="store_true", help="Validate tag coverage without changing files")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.check:
        pages, missing, misplaced, duplicated = audit_google_tags(root)
        if missing or misplaced or duplicated:
            raise SystemExit(
                f"Google tag audit failed: {pages} pages, {len(missing)} missing, "
                f"{len(misplaced)} misplaced, {len(duplicated)} duplicated"
            )
        print(f"Google tag audit passed: {pages} pages tagged once immediately after <head>")
        return
    changed, tagged = install_google_tags(root)
    print(f"Installed Google tag in {changed} pages; {tagged} pages tagged")


if __name__ == "__main__":
    main()
