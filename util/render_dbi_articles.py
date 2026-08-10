#!/usr/bin/env python3
"""Render DBI Services JSON snapshots as self-contained local HTML articles."""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


USER_AGENT = "FranckPachot-blog-archive/1.0"
IMAGE_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?dbi-services\.com/blog/wp-content/uploads/[^\"'<>\s]+",
    re.IGNORECASE,
)
IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".webp"}


def image_signature(path: Path) -> bool:
    header = path.read_bytes()[:16]
    return (
        header.startswith((b"GIF87a", b"GIF89a", b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff"))
        or header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    )


def download_image(url: str, destination: Path) -> bool:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = response.headers.get_content_type()
            if not content_type.startswith("image/"):
                return False
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(response.read())
    except (OSError, urllib.error.URLError):
        return False
    if not image_signature(destination):
        destination.unlink(missing_ok=True)
        return False
    return True


def local_image_path(root: Path, url: str, existing: dict[str, Path]) -> Path | None:
    parsed = urllib.parse.urlsplit(html.unescape(url))
    source_path = Path(urllib.parse.unquote(parsed.path))
    if source_path.suffix.casefold() not in IMAGE_SUFFIXES:
        return None
    destination = root / "dbi-services" / "assets" / source_path.name
    if destination.is_file() and image_signature(destination):
        return destination
    legacy = existing.get(source_path.name.casefold())
    if legacy:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, destination)
        return destination
    if download_image(url, destination):
        return destination
    replay_url = f"https://web.archive.org/web/0id_/{url}"
    if download_image(replay_url, destination):
        return destination
    return None


def replace_missing_image(content: str, url: str) -> str:
    pattern = re.compile(rf"<img\b[^>]*\bsrc=[\"']{re.escape(url)}[\"'][^>]*>", re.IGNORECASE)
    match = pattern.search(content)
    if not match:
        return content
    alt_match = re.search(r"\balt=[\"']([^\"']*)[\"']", match.group(0), re.IGNORECASE)
    replacement = html.escape(html.unescape(alt_match.group(1))) if alt_match else ""
    return content[: match.start()] + replacement + content[match.end() :]


def render_article(root: Path, path: Path, existing: dict[str, Path]) -> tuple[Path, int, int]:
    detail = json.loads(path.read_text(encoding="utf-8"))
    slug = detail["slug"]
    title = detail["title"]["rendered"]
    published = detail["date"][:10]
    canonical = detail["link"]
    content = detail["content"]["rendered"]
    localized = 0
    missing = 0
    for url in sorted(set(IMAGE_URL_PATTERN.findall(content)), key=len, reverse=True):
        image_path = local_image_path(root, url, existing)
        if image_path:
            relative = Path("..", "..", "assets", image_path.name).as_posix()
            content = content.replace(url, relative)
            localized += 1
        else:
            content = replace_missing_image(content, url)
            missing += 1

    output = root / "dbi-services" / "rendered" / slug / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{html.escape(canonical, quote=True)}">
<title>{title}</title>
<link rel="stylesheet" href="../../../style.css">
</head>
<body>
<p class="firstpub">This was first published on <a href="{html.escape(canonical, quote=True)}">{html.escape(canonical)}</a> ({published})<br>Republishing here for new followers. The content is related to the versions available at the publication date.</p>
<h1 class="entry-title">{title}</h1>
<div class="content-inner">
{content}
</div>
</body>
</html>
"""
    document = re.sub(r"[ \t]+(?=\r?$)", "", document, flags=re.MULTILINE)
    output.write_text(document, encoding="utf-8")
    return output, localized, missing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    root = args.root.resolve()
    existing = {
        path.name.casefold(): path
        for path in (root / "2013-2018" / "wp-insides" / "uploads").rglob("*")
        if path.is_file() and path.suffix.casefold() in IMAGE_SUFFIXES
    }
    rendered = localized = missing = 0
    for path in sorted((root / "dbi-services" / "articles").glob("*.json")):
        _, article_localized, article_missing = render_article(root, path, existing)
        rendered += 1
        localized += article_localized
        missing += article_missing
    print(f"Rendered {rendered} DBI articles; localized {localized} image URLs; {missing} unavailable")


if __name__ == "__main__":
    main()