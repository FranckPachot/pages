#!/usr/bin/env python3
"""Inspect PDF text by page or extract a lossless page range."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--find", action="append", default=[])
    parser.add_argument("--pages", help="One-based inclusive range, for example 31-36")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    reader = PdfReader(args.pdf)
    if args.find:
        patterns = [re.compile(pattern, re.IGNORECASE) for pattern in args.find]
        print(f"{args.pdf}: {len(reader.pages)} pages")
        for page_number, page in enumerate(reader.pages, start=1):
            text = re.sub(r"\s+", " ", page.extract_text() or "").strip()
            matches = [pattern.pattern for pattern in patterns if pattern.search(text)]
            if matches:
                print(f"{page_number}: {', '.join(matches)}: {text[:300]}")

    if args.pages:
        if not args.output:
            parser.error("--output is required with --pages")
        match = re.fullmatch(r"(\d+)-(\d+)", args.pages)
        if not match:
            parser.error("--pages must be a one-based inclusive range")
        first, last = map(int, match.groups())
        if first < 1 or last < first or last > len(reader.pages):
            parser.error(f"--pages must be within 1-{len(reader.pages)}")
        writer = PdfWriter()
        for page_index in range(first - 1, last):
            writer.add_page(reader.pages[page_index])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("wb") as output:
            writer.write(output)
        print(f"Wrote {last - first + 1} pages to {args.output}")


if __name__ == "__main__":
    main()