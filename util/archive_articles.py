#!/usr/bin/env python3
"""Inventory local blog exports and incrementally archive online articles."""

from __future__ import annotations

import argparse
import datetime
import html
import json
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEVTO_API = "https://dev.to/api"
DBI_API = "https://www.dbi-services.com/blog/wp-json/wp/v2"
YUGABYTE_API = "https://www.yugabyte.com/wp-json/wp/v2"
TECHCOMMUNITY_BASE = "https://techcommunity.microsoft.com"
CERN_API = "https://db-blog.web.cern.ch/jsonapi/node/blog_post"
CERN_BASE = "https://db-blog.web.cern.ch"
DEVELOPPEZ_BASE = "http://blog.developpez.com/pachot/"
DEVELOPPEZ_CAPTURE = "20120429040723"
DEVELOPPEZ_REPLAY = f"https://web.archive.org/web/{DEVELOPPEZ_CAPTURE}id_/"
USER_AGENT = "FranckPachot-blog-archive/1.0"
DBI_BYLINE_PATTERN = re.compile(
    r"<h2[^>]*>\s*By Franck Pachot\s*</h2>", re.IGNORECASE
)
AWS_ACCESS_KEY_PATTERN = re.compile(r"AKIA[0-9A-Z]{16}")
AWS_SECRET_KEY_PATTERN = re.compile(
    r"((?:aws_secret_access_key|AWS Secret Access Key)(?:\s*\[None\])?\s*[:=]\s*)[A-Za-z0-9/+]{40,44}",
    re.IGNORECASE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def clean_text(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return clean_text(match.group(1)) if match else ""


def sanitize_dbi_detail(detail: dict[str, Any]) -> dict[str, Any]:
    content = detail.get("content", {}).get("rendered", "")
    content = AWS_ACCESS_KEY_PATTERN.sub("REDACTED_AWS_ACCESS_KEY_ID", content)
    content = AWS_SECRET_KEY_PATTERN.sub(r"\1REDACTED_AWS_SECRET_ACCESS_KEY", content)
    detail.get("content", {})["rendered"] = content
    return detail


def write_json_atomic(path: Path, value: Any) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary_path, path)


def write_text_atomic(path: Path, value: str) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(value, encoding="utf-8")
    os.replace(temporary_path, path)


def inventory_legacy_dbi(root: Path) -> list[dict[str, Any]]:
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


def dbi_manifest_entry(root: Path, path: Path, detail: dict[str, Any]) -> dict[str, Any]:
    slug = detail.get("slug", "")
    content = detail.get("content", {}).get("rendered", "")
    if not slug or path.stem != slug:
        raise ValueError(f"Invalid DBI article slug in {path}")
    if not DBI_BYLINE_PATTERN.search(content):
        raise ValueError("Missing exact 'By Franck Pachot' heading")
    if not detail.get("date") or not detail.get("link") or not detail.get("title", {}).get("rendered"):
        raise ValueError(f"Incomplete DBI article metadata in {path}")
    return {
        "source": "dbi-services",
        "source_id": slug,
        "title": clean_text(detail["title"]["rendered"]),
        "published_at": detail["date"],
        "canonical_url": detail["link"],
        "archive_path": path.relative_to(root).as_posix(),
        "tags": [],
    }


def inventory_dbi(root: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted((root / "dbi-services" / "articles").glob("*.json")):
        try:
            detail = json.loads(read_text(path))
            articles.append(dbi_manifest_entry(root, path, detail))
        except (json.JSONDecodeError, ValueError) as error:
            print(f"Skipping invalid DBI snapshot {path.relative_to(root)}: {error}")
    return articles or inventory_legacy_dbi(root)


def list_dbi_articles() -> list[dict[str, Any]]:
    articles = []
    page = 1
    while True:
        query = urllib.parse.urlencode(
            {
                "search": "Franck Pachot",
                "per_page": 100,
                "page": page,
                "_fields": "slug,link,date,title,content",
            }
        )
        batch = web_get_json(f"{DBI_API}/posts?{query}")
        if not isinstance(batch, list):
            raise ValueError(f"Unexpected DBI article list response on page {page}")
        articles.extend(
            article
            for article in batch
            if DBI_BYLINE_PATTERN.search(article.get("content", {}).get("rendered", ""))
        )
        if len(batch) < 100:
            return articles
        page += 1


def archive_dbi(root: Path, refresh: bool) -> list[dict[str, Any]]:
    archive_dir = root / "dbi-services" / "articles"
    archive_dir.mkdir(parents=True, exist_ok=True)
    articles = list_dbi_articles()
    for position, detail in enumerate(articles, start=1):
        detail = sanitize_dbi_detail(detail)
        slug = detail.get("slug", "")
        path = archive_dir / f"{slug}.json"
        dbi_manifest_entry(root, path, detail)
        if refresh or not path.exists():
            write_json_atomic(path, detail)
        print(f"DBI Services {position}/{len(articles)}: {clean_text(detail['title']['rendered'])}")
    return inventory_dbi(root)


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


def web_get(url: str, retries: int = 5) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            if error.code != 429 and error.code < 500:
                raise
            last_error = error
            retry_after = error.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            delay = 2**attempt
        if attempt == retries - 1:
            assert last_error is not None
            raise last_error
        time.sleep(delay + random.random())
    raise RuntimeError("unreachable")


def web_get_json(url: str) -> Any:
    return json.loads(web_get(url))


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


def yugabyte_manifest_entry(root: Path, path: Path, detail: dict[str, Any]) -> dict[str, Any]:
    article_id = detail.get("id")
    if not isinstance(article_id, int) or article_id <= 0:
        raise ValueError(f"Invalid Yugabyte article ID in {path}")
    term_groups = detail.get("_embedded", {}).get("wp:term", [])
    tags = sorted(
        {
            term.get("name", "").strip()
            for group in term_groups
            for term in group
            if term.get("taxonomy") in {"category", "post_tag"} and term.get("name", "").strip()
        }
    )
    return {
        "source": "yugabyte",
        "source_id": str(article_id),
        "title": clean_text(detail.get("title", {}).get("rendered", "")),
        "published_at": detail.get("date_gmt") or detail.get("date", ""),
        "canonical_url": detail.get("link", ""),
        "archive_path": path.relative_to(root).as_posix(),
        "tags": tags,
    }


def inventory_yugabyte(root: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted((root / "yugabyte" / "articles").glob("*.json")):
        try:
            detail = json.loads(read_text(path))
            articles.append(yugabyte_manifest_entry(root, path, detail))
        except (json.JSONDecodeError, ValueError) as error:
            print(f"Skipping invalid Yugabyte snapshot {path.relative_to(root)}: {error}")
    return articles


def list_yugabyte_articles(author_slug: str) -> list[dict[str, Any]]:
    users = web_get_json(f"{YUGABYTE_API}/users?slug={urllib.parse.quote(author_slug)}")
    if not isinstance(users, list) or len(users) != 1 or not isinstance(users[0].get("id"), int):
        raise ValueError(f"Unable to resolve Yugabyte author {author_slug}")
    author_id = users[0]["id"]
    articles = []
    page = 1
    while True:
        url = f"{YUGABYTE_API}/posts?author={author_id}&per_page=100&page={page}&_embed=1"
        batch = web_get_json(url)
        if not isinstance(batch, list):
            raise ValueError(f"Unexpected Yugabyte article list response on page {page}")
        articles.extend(batch)
        if len(batch) < 100:
            return articles
        page += 1


def archive_yugabyte(root: Path, author_slug: str, refresh: bool) -> list[dict[str, Any]]:
    archive_dir = root / "yugabyte" / "articles"
    archive_dir.mkdir(parents=True, exist_ok=True)
    summaries = list_yugabyte_articles(author_slug)
    for position, detail in enumerate(summaries, start=1):
        article_id = detail.get("id")
        if not isinstance(article_id, int) or article_id <= 0:
            raise ValueError("Invalid Yugabyte article response")
        path = archive_dir / f"{article_id}.json"
        replace_snapshot = refresh or not path.exists()
        if not replace_snapshot:
            try:
                yugabyte_manifest_entry(root, path, json.loads(read_text(path)))
            except (json.JSONDecodeError, ValueError):
                replace_snapshot = True
        if replace_snapshot:
            yugabyte_manifest_entry(root, path, detail)
            write_json_atomic(path, detail)
        print(f"Yugabyte {position}/{len(summaries)}: {clean_text(detail['title']['rendered'])}")
    return inventory_yugabyte(root)


def jsonld_values(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for nested in value for item in jsonld_values(nested)]
    if not isinstance(value, dict):
        return []
    graph = value.get("@graph")
    return jsonld_values(graph) if graph is not None else [value]


def techcommunity_metadata(document: str) -> dict[str, Any] | None:
    for raw_value in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        document,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            continue
        for item in jsonld_values(value):
            item_types = item.get("@type", [])
            if isinstance(item_types, str):
                item_types = [item_types]
            if "BlogPosting" in item_types:
                return item
    return None


def techcommunity_manifest_entry(
    root: Path, path: Path, document: str, author_name: str, profile_id: str
) -> dict[str, Any]:
    metadata = techcommunity_metadata(document)
    if not metadata:
        raise ValueError("Missing BlogPosting metadata")
    authors = metadata.get("author", [])
    if isinstance(authors, dict):
        authors = [authors]
    if not isinstance(authors, list) or not any(
        isinstance(author, dict) and author.get("name", "").casefold() == author_name.casefold()
        for author in authors
    ):
        raise ValueError(f"Article is not authored by {author_name}")
    if profile_id not in document:
        raise ValueError(f"Article does not reference profile {profile_id}")
    main_entity = metadata.get("mainEntityOfPage", "")
    canonical = main_entity.get("@id", "") if isinstance(main_entity, dict) else main_entity
    article_id_match = re.search(r"/(\d+)$", canonical)
    if not article_id_match or article_id_match.group(1) != path.stem:
        raise ValueError("Invalid Microsoft Tech Community article ID")
    published = datetime.datetime.strptime(metadata["datePublished"], "%m/%d/%Y, %I:%M:%S %p")
    return {
        "source": "microsoft-techcommunity",
        "source_id": path.stem,
        "title": clean_text(metadata.get("headline", "")),
        "published_at": published.isoformat(),
        "canonical_url": canonical,
        "archive_path": path.relative_to(root).as_posix(),
        "tags": [],
    }


def inventory_techcommunity(
    root: Path, author_name: str, profile_id: str
) -> list[dict[str, Any]]:
    articles = []
    for path in sorted((root / "microsoft-techcommunity" / "articles").glob("*.html")):
        try:
            document = read_text(path)
            articles.append(techcommunity_manifest_entry(root, path, document, author_name, profile_id))
        except ValueError as error:
            print(f"Skipping invalid Microsoft snapshot {path.relative_to(root)}: {error}")
    return articles


def list_techcommunity_articles(author_name: str) -> list[str]:
    article_urls: set[str] = set()
    expected_count: int | None = None
    for page in range(1, 101):
        query = urllib.parse.urlencode({"q": author_name, "page": page})
        document = web_get(f"{TECHCOMMUNITY_BASE}/search?{query}")
        count_match = re.search(r"\b(\d+)\s+Results?\b", document, re.IGNORECASE)
        if count_match:
            expected_count = int(count_match.group(1))
        page_urls = {
            urllib.parse.urljoin(TECHCOMMUNITY_BASE, value)
            for value in re.findall(
                r'href=["\']((?:https://techcommunity\.microsoft\.com)?/blog/[^"\']+?/\d+)["\']',
                document,
                re.IGNORECASE,
            )
        }
        new_urls = page_urls - article_urls
        article_urls.update(page_urls)
        if expected_count is not None and len(article_urls) >= expected_count:
            break
        if not new_urls:
            if expected_count is not None and len(article_urls) < expected_count:
                raise ValueError(
                    f"Microsoft search reported {expected_count} results but only "
                    f"{len(article_urls)} article URLs were discovered"
                )
            break
    return sorted(article_urls)


def archive_techcommunity(
    root: Path, author_name: str, profile_id: str, refresh: bool
) -> list[dict[str, Any]]:
    archive_dir = root / "microsoft-techcommunity" / "articles"
    archive_dir.mkdir(parents=True, exist_ok=True)
    candidates = list_techcommunity_articles(author_name)
    for path in archive_dir.glob("*.html"):
        metadata = techcommunity_metadata(read_text(path))
        main_entity = metadata.get("mainEntityOfPage", "") if metadata else ""
        canonical = main_entity.get("@id", "") if isinstance(main_entity, dict) else main_entity
        if isinstance(canonical, str) and canonical.startswith(TECHCOMMUNITY_BASE):
            candidates.append(canonical)
    archived = 0
    for url in sorted(set(candidates)):
        article_id = url.rstrip("/").rsplit("/", 1)[-1]
        if not article_id.isdigit():
            continue
        path = archive_dir / f"{article_id}.html"
        replace_snapshot = refresh or not path.exists()
        document = web_get(url) if replace_snapshot else read_text(path)
        try:
            entry = techcommunity_manifest_entry(root, path, document, author_name, profile_id)
        except ValueError:
            if replace_snapshot:
                continue
            document = web_get(url)
            try:
                entry = techcommunity_manifest_entry(root, path, document, author_name, profile_id)
            except ValueError:
                continue
            replace_snapshot = True
        if replace_snapshot:
            write_text_atomic(path, document)
        archived += 1
        print(f"Microsoft Tech Community {archived}: {entry['title']}")
    return inventory_techcommunity(root, author_name, profile_id)


def cern_manifest_entry(root: Path, path: Path, detail: dict[str, Any]) -> dict[str, Any]:
    attributes = detail.get("attributes", {})
    article_id = attributes.get("drupal_internal__nid")
    alias = attributes.get("path", {}).get("alias", "")
    if not isinstance(article_id, int) or article_id <= 0 or path.stem != str(article_id):
        raise ValueError(f"Invalid CERN article ID in {path}")
    if not attributes.get("title") or not attributes.get("created") or not alias.startswith("/blog/"):
        raise ValueError(f"Incomplete CERN article metadata in {path}")
    return {
        "source": "cern",
        "source_id": str(article_id),
        "title": clean_text(attributes["title"]),
        "published_at": attributes["created"],
        "canonical_url": urllib.parse.urljoin(CERN_BASE, alias),
        "archive_path": path.relative_to(root).as_posix(),
        "tags": [],
    }


def inventory_cern(root: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted((root / "cern" / "articles").glob("*.json")):
        try:
            detail = json.loads(read_text(path))
            articles.append(cern_manifest_entry(root, path, detail))
        except (json.JSONDecodeError, ValueError) as error:
            print(f"Skipping invalid CERN snapshot {path.relative_to(root)}: {error}")
    return articles


def developpez_manifest_entry(root: Path, path: Path, document: str) -> dict[str, Any]:
    article_id_match = re.search(r"/p(\d+)/", document)
    title = first_match(r'<h[1-4][^>]+class="[^"]*bTitle[^"]*"[^>]*>(.*?)</h[1-4]>', document)
    if not title:
        title = first_match(r"<title>\s*Article complet:\s*(.*?)</title>", document)
    published_match = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", document)
    canonical = first_match(
        r'<a[^>]+href="(http://blog\.developpez\.com/pachot/p\d+/[^"#?]+/)"[^>]+title="Lien permanent',
        document,
    )
    if not article_id_match or path.stem != article_id_match.group(1):
        raise ValueError(f"Invalid Developpez article ID in {path}")
    if not title or not published_match or not canonical:
        raise ValueError(f"Incomplete Developpez article metadata in {path}")
    if "Pachot Franck" not in document or "French (FR" not in document:
        raise ValueError(f"Unverified Developpez author or language in {path}")
    day, month, year = published_match.groups()
    return {
        "source": "developpez",
        "source_id": article_id_match.group(1),
        "title": title,
        "published_at": f"{year}-{month}-{day}",
        "canonical_url": canonical,
        "archive_path": path.relative_to(root).as_posix(),
        "language": "fr",
        "tags": [],
    }


def inventory_developpez(root: Path) -> list[dict[str, Any]]:
    articles = []
    for path in sorted((root / "developpez" / "articles").glob("*.html")):
        try:
            articles.append(developpez_manifest_entry(root, path, read_text(path)))
        except ValueError as error:
            print(f"Skipping invalid Developpez snapshot {path.relative_to(root)}: {error}")
    return articles


def list_developpez_articles() -> list[str]:
    articles: set[str] = set()
    month = datetime.date(2010, 3, 28)
    final_month = datetime.date(2011, 6, 28)
    while month <= final_month:
        capture = month.strftime("%Y%m%d")
        feed_url = "http://blog.developpez.com/xmlsrv/atom.php?blog=337"
        document = web_get(f"https://web.archive.org/web/{capture}id_/{feed_url}")
        articles.update(
            match.rstrip("/") + "/"
            for match in re.findall(
                r"http://blog\.developpez\.com/pachot/p\d+/[^\"'?#< ]+", document
            )
        )
        if month.month == 12:
            month = datetime.date(month.year + 1, 1, 28)
        else:
            month = datetime.date(month.year, month.month + 1, 28)
    if len(articles) != 41:
        raise ValueError(f"Expected 41 Developpez articles, found {len(articles)}")
    return sorted(articles, key=lambda url: int(re.search(r"/p(\d+)/", url).group(1)))


def archive_developpez(root: Path, refresh: bool) -> list[dict[str, Any]]:
    archive_dir = root / "developpez" / "articles"
    archive_dir.mkdir(parents=True, exist_ok=True)
    articles = list_developpez_articles()
    for position, url in enumerate(articles, start=1):
        article_id = re.search(r"/p(\d+)/", url).group(1)
        path = archive_dir / f"{article_id}.html"
        document = web_get(f"{DEVELOPPEZ_REPLAY}{url}") if refresh or not path.exists() else read_text(path)
        entry = developpez_manifest_entry(root, path, document)
        if refresh or not path.exists():
            write_text_atomic(path, document)
        print(f"Developpez {position}/{len(articles)}: {entry['title']}")
    return inventory_developpez(root)


def list_cern_articles(author_username: str) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {"filter[uid.name]": author_username, "page[limit]": 50}
    )
    response = web_get_json(f"{CERN_API}?{query}")
    articles = response.get("data") if isinstance(response, dict) else None
    if not isinstance(articles, list) or response.get("links", {}).get("next"):
        raise ValueError("Unexpected or paginated CERN article response")
    return articles


def archive_cern(root: Path, author_username: str, refresh: bool) -> list[dict[str, Any]]:
    archive_dir = root / "cern" / "articles"
    archive_dir.mkdir(parents=True, exist_ok=True)
    articles = list_cern_articles(author_username)
    for position, detail in enumerate(articles, start=1):
        article_id = detail.get("attributes", {}).get("drupal_internal__nid")
        if not isinstance(article_id, int) or article_id <= 0:
            raise ValueError("Invalid CERN article response")
        path = archive_dir / f"{article_id}.json"
        cern_manifest_entry(root, path, detail)
        if refresh or not path.exists():
            write_json_atomic(path, detail)
        print(f"CERN {position}/{len(articles)}: {clean_text(detail['attributes']['title'])}")
    return inventory_cern(root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--username", default="franckpachot")
    parser.add_argument("--skip-dbi", action="store_true")
    parser.add_argument("--refresh-dbi", action="store_true")
    parser.add_argument("--skip-devto", action="store_true")
    parser.add_argument("--refresh-devto", action="store_true")
    parser.add_argument("--max-devto", type=int, help="Limit Dev.to downloads for testing")
    parser.add_argument("--skip-yugabyte", action="store_true")
    parser.add_argument("--refresh-yugabyte", action="store_true")
    parser.add_argument("--skip-techcommunity", action="store_true")
    parser.add_argument("--refresh-techcommunity", action="store_true")
    parser.add_argument("--skip-cern", action="store_true")
    parser.add_argument("--refresh-cern", action="store_true")
    parser.add_argument("--skip-developpez", action="store_true")
    parser.add_argument("--refresh-developpez", action="store_true")
    parser.add_argument("--yugabyte-author", default="fpachot")
    parser.add_argument("--techcommunity-author", default="FranckPachot")
    parser.add_argument("--techcommunity-profile-id", default="3595257")
    parser.add_argument("--cern-author", default="fpachot")
    parser.add_argument("--offline", action="store_true", help="Rebuild from local snapshots only")
    args = parser.parse_args()

    if args.offline:
        args.skip_dbi = True
        args.skip_devto = True
        args.skip_yugabyte = True
        args.skip_techcommunity = True
        args.skip_cern = True
        args.skip_developpez = True

    root = args.root.resolve()
    if not args.skip_dbi:
        articles = archive_dbi(root, args.refresh_dbi)
    else:
        articles = inventory_dbi(root)
    articles += inventory_medium(root)
    if not args.skip_devto:
        articles += archive_devto(root, args.username, args.refresh_devto, args.max_devto)
    else:
        articles += inventory_devto(root)
    if not args.skip_yugabyte:
        articles += archive_yugabyte(root, args.yugabyte_author, args.refresh_yugabyte)
    else:
        articles += inventory_yugabyte(root)
    if not args.skip_techcommunity:
        articles += archive_techcommunity(
            root,
            args.techcommunity_author,
            args.techcommunity_profile_id,
            args.refresh_techcommunity,
        )
    else:
        articles += inventory_techcommunity(
            root, args.techcommunity_author, args.techcommunity_profile_id
        )
    if not args.skip_cern:
        articles += archive_cern(root, args.cern_author, args.refresh_cern)
    else:
        articles += inventory_cern(root)
    if not args.skip_developpez:
        articles += archive_developpez(root, args.refresh_developpez)
    else:
        articles += inventory_developpez(root)
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