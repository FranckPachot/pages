#!/usr/bin/env python3
"""Regression checks for publication archive discovery."""

import urllib.error
from unittest.mock import patch

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

    def article(article_id: int) -> dict:
        return {"id": article_id, "user": {"username": "franckpachot"}}

    with patch.object(
        archive_articles,
        "api_get",
        side_effect=[[article(3), article(2)], [article(2), article(1)], []],
    ) as request:
        assert [item["id"] for item in archive_articles.list_devto_articles("franckpachot")] == [3, 2, 1]
        assert [call.args[0] for call in request.call_args_list] == [
            f"/articles/latest?username=franckpachot&per_page=100&page={page}"
            for page in (1, 2, 3)
        ]

    for batches, message in (
        ([[article(1)], [article(1)]], "no progress"),
        ([[{"id": 1, "user": {"username": "another-author"}}]], "author"),
    ):
        with patch.object(archive_articles, "api_get", side_effect=batches):
            try:
                archive_articles.list_devto_articles("franckpachot")
            except ValueError as error:
                assert message in str(error)
            else:
                raise AssertionError("Invalid DEV pagination must be rejected")


if __name__ == "__main__":
    main()
