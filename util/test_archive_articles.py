#!/usr/bin/env python3
"""Regression checks for publication archive discovery."""

import urllib.error

import archive_articles


def main() -> None:
    calls = []
    summary = {
        "id": 42,
        "path": "/example/article-slug",
    }

    def fake_api_get(path: str):
        calls.append(path)
        if path == "/articles/42":
            raise urllib.error.HTTPError(path, 404, "Not Found", {}, None)
        return {"id": 42, "title": "Article"}

    original_api_get = archive_articles.api_get
    archive_articles.api_get = fake_api_get
    try:
        assert archive_articles.get_devto_article_detail(summary)["id"] == 42
    finally:
        archive_articles.api_get = original_api_get

    assert calls == ["/articles/42", "/articles/example/article-slug"]


if __name__ == "__main__":
    main()
