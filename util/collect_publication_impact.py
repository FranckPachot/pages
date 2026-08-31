#!/usr/bin/env python3
"""Collect dated publication impact metrics without modifying article snapshots."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEVTO_API = "https://dev.to/api"
USER_AGENT = "FranckPachot-blog-archive/1.0"
API_KEY_ENV = "BLOG_ARCHIVE_DEVTO_API_KEY"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(temporary_path, path)


def required_total(group: Any, group_name: str) -> int:
    if not isinstance(group, dict) or not isinstance(group.get("total"), int):
        raise ValueError(f"Dev.to analytics response has no integer {group_name}.total")
    return group["total"]


def normalize_devto_totals(
    article: dict[str, Any], totals: dict[str, Any], collected_at: str
) -> dict[str, Any]:
    article_id = article.get("id")
    if not isinstance(article_id, int) or article_id <= 0:
        raise ValueError("Invalid Dev.to article ID")

    page_views = totals.get("page_views")
    reactions = totals.get("reactions")
    if not isinstance(page_views, dict) or not isinstance(reactions, dict):
        raise ValueError("Incomplete Dev.to analytics response")

    return {
        "publication_id": f"dev.to:{article_id}",
        "source": "dev.to",
        "source_id": str(article_id),
        "title": article.get("title", ""),
        "canonical_url": article.get("canonical_url") or article.get("url", ""),
        "published_at": article.get("published_at", ""),
        "collected_at": collected_at,
        "metrics": {
            "page_views": required_total(page_views, "page_views"),
            "average_read_time_seconds": page_views.get("average_read_time_in_seconds"),
            "total_read_time_seconds": page_views.get("total_read_time_in_seconds"),
            "reactions": required_total(reactions, "reactions"),
            "unique_reactors": reactions.get("unique_reactors"),
            "comments": required_total(totals.get("comments"), "comments"),
        },
        "public_counters": {
            "reactions": article.get("public_reactions_count"),
            "comments": article.get("comments_count"),
        },
        "provenance": {
            "measurement_type": "exact",
            "provider": "DEV Community authenticated analytics API",
            "endpoint": f"/api/analytics/totals?article_id={article_id}",
            "notes": "The API's follows total is author-wide and is intentionally omitted.",
        },
    }


def merge_publications(
    existing: list[dict[str, Any]], collected: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    publications = {
        publication["publication_id"]: publication
        for publication in existing
        if isinstance(publication, dict) and isinstance(publication.get("publication_id"), str)
    }
    publications.update(
        {publication["publication_id"]: publication for publication in collected}
    )
    return [publications[publication_id] for publication_id in sorted(publications)]


def devto_get(path: str, api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{DEVTO_API}{path}",
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "api-key": api_key,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError(f"Unexpected Dev.to response for {path}")
    return value


def local_devto_articles(root: Path, article_ids: list[int], collect_all: bool) -> list[dict[str, Any]]:
    requested_ids = set(article_ids)
    articles = []
    for path in sorted((root / "devto" / "articles").glob("*.json")):
        article = read_json(path)
        if collect_all or article.get("id") in requested_ids:
            articles.append(article)
    found_ids = {article.get("id") for article in articles}
    missing_ids = requested_ids - found_ids
    if missing_ids:
        raise ValueError(f"No local Dev.to snapshot for article IDs: {sorted(missing_ids)}")
    return articles


def collect_devto(
    root: Path, article_ids: list[int], collect_all: bool, request_interval: float
) -> Path:
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise ValueError(
            f"Set {API_KEY_ENV} in the process environment; do not pass API keys on the command line."
        )

    articles = local_devto_articles(root, article_ids, collect_all)
    if not articles:
        raise ValueError("Specify at least one --article-id or use --all-devto")

    collected_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    publications = []
    for position, article in enumerate(articles, start=1):
        article_id = article["id"]
        query = urllib.parse.urlencode({"article_id": article_id})
        totals = devto_get(f"/analytics/totals?{query}", api_key)
        publications.append(normalize_devto_totals(article, totals, collected_at))
        print(f"Dev.to impact {position}/{len(articles)}: {article.get('title', article_id)}")
        if position < len(articles):
            time.sleep(request_interval)

    snapshot = {
        "schema_version": 1,
        "collected_at": collected_at,
        "publication_count": len(publications),
        "publications": publications,
    }
    day = collected_at[:10]
    output_path = root / "impact" / "devto" / f"{day}.json"
    if output_path.exists():
        existing = read_json(output_path)
        snapshot["publications"] = merge_publications(
            existing.get("publications", []), publications
        )
        snapshot["publication_count"] = len(snapshot["publications"])
    write_json_atomic(output_path, snapshot)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--article-id", type=int, action="append", default=[])
    parser.add_argument("--all-devto", action="store_true")
    parser.add_argument(
        "--request-interval",
        type=float,
        default=2.1,
        help="Seconds between requests; the default stays below DEV's 30 requests/minute limit.",
    )
    args = parser.parse_args()
    if args.request_interval < 2:
        parser.error("--request-interval must be at least 2 seconds")
    output_path = collect_devto(
        args.root.resolve(), args.article_id, args.all_devto, args.request_interval
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
