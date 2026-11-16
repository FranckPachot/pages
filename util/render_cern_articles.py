#!/usr/bin/env python3
"""Render CERN snapshots and link Medium announcements to the local articles."""

from __future__ import annotations

import html
import json
import os
import re
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from archive_articles import CERN_BASE, write_text_atomic
from google_analytics import add_google_tag
from render_dbi_articles import download_image, image_signature


NOTICE_PATTERN = re.compile(
    r"\n?<!-- BEGIN CERN ARCHIVE LINKS -->.*?<!-- END CERN ARCHIVE LINKS -->\n?",
    re.DOTALL,
)


def without_cern_notice(document: str) -> str:
    return NOTICE_PATTERN.sub("", document)


def cern_url_key(url: str) -> str:
    parsed = urllib.parse.urlsplit(html.unescape(url))
    return f"{parsed.netloc.casefold()}{parsed.path.rstrip('/')}"


def reader_path(article: dict[str, Any]) -> str:
    return f"cern/rendered/{article['source_id']}/index.html"


class CernLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href and urllib.parse.urlsplit(href).hostname == "db-blog.web.cern.ch":
                self.urls.append(href)


def cern_references(
    document: str, articles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_url = {cern_url_key(article["canonical_url"]): article for article in articles}
    parser = CernLinks()
    parser.feed(without_cern_notice(document))
    references = {}
    for url in parser.urls:
        article = by_url.get(cern_url_key(url))
        if article:
            references[article["source_id"]] = article
    return list(references.values())


def render_cern_articles(root: Path, manifest: list[dict[str, Any]]) -> tuple[int, int]:
    articles = [article for article in manifest if article["source"] == "cern"]
    by_url = {cern_url_key(article["canonical_url"]): article for article in articles}
    for article in articles:
        detail = json.loads((root / article["archive_path"]).read_text(encoding="utf-8"))
        content = detail["attributes"]["body"]["processed"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"Missing CERN article body: {article['archive_path']}")
        output = root / reader_path(article)

        def resolve_url(match: re.Match[str]) -> str:
            attribute, quote, original = match.groups()
            url = urllib.parse.urljoin(article["canonical_url"], html.unescape(original))
            parsed = urllib.parse.urlsplit(url)
            if attribute.casefold() == "src" and parsed.hostname == "db-blog-multimedia.web.cern.ch":
                asset = root / "cern" / "assets" / Path(parsed.path).name
                if not asset.is_file() or not image_signature(asset):
                    secure_url = urllib.parse.urlunsplit(parsed._replace(scheme="https"))
                    if not download_image(secure_url, asset):
                        raise RuntimeError(f"Unable to archive CERN image: {secure_url}")
                url = Path(os.path.relpath(asset, output.parent)).as_posix()
            elif attribute.casefold() == "href" and cern_url_key(url) in by_url:
                target = root / reader_path(by_url[cern_url_key(url)])
                url = Path(os.path.relpath(target, output.parent)).as_posix()
                if parsed.fragment:
                    url += f"#{parsed.fragment}"
            return f"{attribute}={quote}{html.escape(url, quote=True)}{quote}"

        content = re.sub(r'\b(href|src)=(["\'])(.*?)\2', resolve_url, content, flags=re.IGNORECASE)
        canonical = html.escape(article["canonical_url"], quote=True)
        title = html.escape(article["title"])
        published = article["published_at"][:10]
        document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="{canonical}">
<title>{title}</title>
<link rel="stylesheet" href="../../../style.css">
</head>
<body>
<nav><a href="../../../index.html">Publication index</a></nav>
<p class="firstpub">Archived from Databases at CERN, published {published}.
<a href="{canonical}">Original article URL</a>.
The content describes the versions available at the publication date.</p>
<h1>{title}</h1>
<main>
{content}
</main>
</body>
</html>
"""
        document = re.sub(r"[ \t]+(?=\r?$)", "", document, flags=re.MULTILINE)
        output.parent.mkdir(parents=True, exist_ok=True)
        write_text_atomic(output, add_google_tag(document))

    linked = 0
    for article in manifest:
        if article["source"] != "medium":
            continue
        path = root / article["archive_path"]
        document = path.read_text(encoding="utf-8")
        references = cern_references(document, articles)
        if not references:
            continue
        links = []
        for reference in references:
            target = root / reader_path(reference)
            url = Path(os.path.relpath(target, path.parent)).as_posix()
            links.append(f'<li><a href="{url}">{html.escape(reference["title"])}</a></li>')
        notice = (
            '<!-- BEGIN CERN ARCHIVE LINKS -->\n'
            '<aside aria-label="Archived CERN articles" style="box-sizing:border-box;'
            'max-width:640px;margin:24px auto;padding:16px;border:1px solid #006b62;'
            'background:#f7f8f5">'
            '<strong>Read the full archived CERN article</strong>'
            '<p>This Medium post references CERN content preserved in this archive. '
            'The original CERN website may no longer be available.</p>'
            f'<ul>{"".join(links)}</ul></aside>\n'
            '<!-- END CERN ARCHIVE LINKS -->\n'
        )
        updated, count = re.subn(
            r"(<body\b[^>]*>)",
            lambda match: match.group(1) + "\n" + notice,
            without_cern_notice(document),
            count=1,
            flags=re.IGNORECASE,
        )
        if count != 1:
            raise ValueError(f"Missing Medium document body: {article['archive_path']}")
        if updated != document:
            write_text_atomic(path, updated)
        linked += 1
    return len(articles), linked
