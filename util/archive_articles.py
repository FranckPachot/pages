#!/usr/bin/env python3
"""Inventory local blog exports and incrementally archive Dev.to articles."""

from __future__ import annotations

import argparse
import html
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEVTO_API = "https://dev.to/api"
USER_AGENT = "FranckPachot-blog-archive/1.0"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def clean_text(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return clean_text(match.group(1)) if match else ""


def write_json_atomic(path: Path, value: Any) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary_path, path)


def inventory_dbi(root: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted((root / "2013-2018").glob("*/index.html")):
        document = read_text(path)
        canonical = first_match(r"<link\s+rel=canonical\s+href=([^\s>]+)", document)
        published = first_match(r"This was first published on .*?\((\d{4}-\d{2}-\d{2})\)", document)
        title = first_match(r'<h1\s+class="entry-title">(.*?)</h1>', document)
        if not title or not published or not re.fullmatch(r"https?://.+", canonical):
            print(f"Skipping non-article DBI page: {path.relative_to(root)}")
            continue
        articles.append(
            {
                "source": "dbi-services",
                "source_id": path.parent.name,
                "title": title,
                "published_at": published,
                "canonical_url": canonical,
                "archive_path": path.relative_to(root).as_posix(),
                "tags": [],
            }
        )
    return articles


def inventory_medium(root: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted((root / "2018-medium" / "posts").glob("*.html")):
        if path.name == "index.html" or path.name.startswith("draft_"):
            continue
        document = read_text(path)
        canonical = first_match(r'<a\s+href="([^"]+)"\s+class="p-canonical"', document)
        published = first_match(r'<time\s+class="dt-published"\s+datetime="([^"]+)"', document)
        title = first_match(r'<h1\s+class="p-name">(.*?)</h1>', document)
        source_id = first_match(r'href="https?://medium\.com/p/([0-9a-f]+)"', document)
        if not source_id:
            source_id_match = re.search(r"-([0-9a-f]+)\.html$", path.name)
            source_id = source_id_match.group(1) if source_id_match else path.stem
        if not title or not published or not canonical:
            print(f"Skipping malformed Medium article: {path.relative_to(root)}")
            continue
        articles.append(
            {
                "source": "medium",
                "source_id": source_id,
                "title": title,
                "published_at": published,
                "canonical_url": canonical,
                "archive_path": path.relative_to(root).as_posix(),
                "tags": [],
            }
        )
    return articles


def api_get(path: str, retries: int = 5) -> Any:
    request = urllib.request.Request(
        f"{DEVTO_API}{path}", headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 and error.code < 500:
                raise
            last_error = error
            retry_after = error.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            delay = 2**attempt
        if attempt == retries - 1:
            assert last_error is not None
            raise last_error
        time.sleep(delay + random.random())
    raise RuntimeError("unreachable")


def list_devto_articles(username: str) -> list[dict[str, Any]]:
    articles = []
    page = 1
    while True:
        batch = api_get(f"/articles?username={username}&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError(f"Unexpected Dev.to article list response on page {page}")
        if not batch:
            return articles
        if not all(isinstance(article.get("id"), int) and article["id"] > 0 for article in batch):
            raise ValueError(f"Invalid Dev.to article ID on page {page}")
        articles.extend(batch)
        page += 1


def devto_manifest_entry(root: Path, path: Path, detail: dict[str, Any]) -> dict[str, Any]:
    article_id = detail.get("id")
    if not isinstance(article_id, int) or article_id <= 0:
        raise ValueError(f"Invalid Dev.to article ID in {path}")
    tags = detail.get("tags", detail.get("tag_list", []))
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
    return {
        "source": "dev.to",
        "source_id": str(article_id),
        "title": detail.get("title", ""),
        "published_at": detail.get("published_at", ""),
        "canonical_url": detail.get("canonical_url") or detail.get("url", ""),
        "archive_path": path.relative_to(root).as_posix(),
        "tags": tags,
    }


def inventory_devto(root: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted((root / "devto" / "articles").glob("*.json")):
        try:
            detail = json.loads(read_text(path))
            articles.append(devto_manifest_entry(root, path, detail))
        except (json.JSONDecodeError, ValueError) as error:
            print(f"Skipping invalid Dev.to snapshot {path.relative_to(root)}: {error}")
    return articles


def archive_devto(
    root: Path, username: str, refresh: bool, max_articles: int | None
) -> list[dict[str, Any]]:
    archive_dir = root / "devto" / "articles"
    archive_dir.mkdir(parents=True, exist_ok=True)
    summaries = list_devto_articles(username)
    if max_articles is not None:
        summaries = summaries[:max_articles]

    articles = []
    for position, summary in enumerate(summaries, start=1):
        article_id = str(summary["id"])
        path = archive_dir / f"{article_id}.json"
        if refresh or not path.exists():
            detail = api_get(f"/articles/{article_id}")
            if not isinstance(detail, dict) or detail.get("id") != summary["id"]:
                raise ValueError(f"Unexpected Dev.to detail response for article {article_id}")
            write_json_atomic(path, detail)
        else:
            try:
                detail = json.loads(read_text(path))
            except json.JSONDecodeError:
                detail = api_get(f"/articles/{article_id}")
                write_json_atomic(path, detail)
        devto_manifest_entry(root, path, detail)
        print(f"Dev.to {position}/{len(summaries)}: {detail.get('title', article_id)}")
    return inventory_devto(root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--username", default="franckpachot")
    parser.add_argument("--skip-devto", action="store_true")
    parser.add_argument("--refresh-devto", action="store_true")
    parser.add_argument("--max-devto", type=int, help="Limit Dev.to downloads for testing")
    args = parser.parse_args()

    root = args.root.resolve()
    articles = inventory_dbi(root) + inventory_medium(root)
    if not args.skip_devto:
        articles += archive_devto(root, args.username, args.refresh_devto, args.max_devto)
    else:
        articles += inventory_devto(root)
    articles.sort(key=lambda article: (article["published_at"], article["source"]), reverse=True)

    manifest = {
        "schema_version": 1,
        "article_count": len(articles),
        "sources": {
            source: sum(article["source"] == source for article in articles)
            for source in sorted({article["source"] for article in articles})
        },
        "articles": articles,
    }
    manifest_path = root / "archive-manifest.json"
    write_json_atomic(manifest_path, manifest)
    print(f"Wrote {manifest_path} with {len(articles)} articles")


if __name__ == "__main__":
    main()