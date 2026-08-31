#!/usr/bin/env python3
"""Regression checks for the publication impact dashboard."""

import json
import tempfile
from pathlib import Path

from build_impact_page import article_views, build_document, latest_observations


def write_snapshot(root: Path, source: str, date: str, publications: list[dict]) -> None:
    directory = root / "impact" / source
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{date}.json").write_text(
        json.dumps({"schema_version": 1, "publications": publications}),
        encoding="utf-8",
    )


def main() -> None:
    devto = {
        "publication_id": "dev.to:1",
        "source": "dev.to",
        "title": "DEV article",
        "canonical_url": "https://dev.to/example",
        "published_at": "2026-01-01",
        "metrics": {"page_views": 10},
    }
    linkedin = {
        "publication_id": "linkedin:1",
        "source": "linkedin",
        "title": "LinkedIn article",
        "canonical_url": "https://www.linkedin.com/pulse/example",
        "published_at": "2026-01-02",
        "metrics": {"article_views": 3, "feed_post_impressions": 1000},
    }

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        write_snapshot(
            root,
            "devto",
            "2026-01-01",
            [{**devto, "collected_at": "2026-01-01T12:00:00Z"}],
        )
        write_snapshot(
            root,
            "devto",
            "2026-01-02",
            [{**devto, "collected_at": "2026-01-02T12:00:00Z", "metrics": {"page_views": 12}}],
        )
        write_snapshot(
            root,
            "linkedin",
            "2026-01-02",
            [{**linkedin, "collected_at": "2026-01-02T12:00:00Z"}],
        )

        publications = latest_observations(root)
        assert len(publications) == 2
        assert next(item for item in publications if item["source"] == "dev.to")["metrics"]["page_views"] == 12
        assert article_views(linkedin) == 3

        document = build_document(publications, {"dev.to": 20, "linkedin": 5})
        assert "2 / 25" in document
        assert "1 / 20" in document
        assert "1 / 5" in document
        assert "1,000</strong>" in document
        assert "15</strong>" in document
        assert "1,015</strong>" not in document
        assert 'data-views="3"' in document
        assert "Article views measure opened articles" in document


if __name__ == "__main__":
    main()
