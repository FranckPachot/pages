#!/usr/bin/env python3
"""Regression checks for publication impact normalization."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from collect_publication_impact import (
    collect_devto_public,
    merge_publications,
    normalize_devto_public,
    normalize_devto_totals,
)


def main() -> None:
    article = {
        "id": 4528531,
        "title": "PostgreSQL INCLUDE indexes: what problem are they trying to solve?",
        "canonical_url": "https://dev.to/franckpachot/postgresql-include-indexes-what-problem-are-they-trying-to-solve-4f4n",
        "published_at": "2026-08-31T13:42:16Z",
        "public_reactions_count": 2,
        "comments_count": 0,
        "user": {"username": "franckpachot"},
    }
    totals = {
        "comments": {"total": 1},
        "follows": {"total": 23430},
        "reactions": {"total": 2, "unique_reactors": 1},
        "page_views": {
            "total": 17,
            "average_read_time_in_seconds": 197,
            "total_read_time_in_seconds": 3349,
        },
    }

    impact = normalize_devto_totals(article, totals, "2026-08-31T16:00:00Z")
    assert impact["publication_id"] == "dev.to:4528531"
    assert impact["metrics"] == {
        "page_views": 17,
        "average_read_time_seconds": 197,
        "total_read_time_seconds": 3349,
        "reactions": 2,
        "unique_reactors": 1,
        "comments": 1,
    }
    assert impact["public_counters"] == {"reactions": 2, "comments": 0}
    assert "follows" not in impact["metrics"]
    assert impact["provenance"]["measurement_type"] == "exact"

    public = normalize_devto_public(article, "2026-09-29T07:00:00Z")
    assert public["metrics"] == {}
    assert public["public_counters"] == {"reactions": 2, "comments": 0}
    assert public["provenance"]["measurement_type"] == "public_counter"
    assert public["provenance"]["endpoint"] == "/api/articles/latest"

    with tempfile.TemporaryDirectory() as temporary_directory:
        with patch("collect_publication_impact.list_devto_articles", return_value=[article]) as discover:
            output = collect_devto_public(Path(temporary_directory), "franckpachot")
        discover.assert_called_once_with("franckpachot")
        snapshot = json.loads(output.read_text(encoding="utf-8"))
        assert snapshot["publication_count"] == 1
        assert snapshot["publications"][0]["metrics"] == {}
        assert snapshot["publications"][0]["public_counters"] == {"reactions": 2, "comments": 0}

    older = {**impact, "collected_at": "2026-08-31T15:00:00Z"}
    other = {**impact, "publication_id": "dev.to:123", "source_id": "123"}
    merged = merge_publications([older, other], [impact])
    assert [publication["publication_id"] for publication in merged] == [
        "dev.to:123",
        "dev.to:4528531",
    ]
    assert merged[1]["collected_at"] == "2026-08-31T16:00:00Z"

    try:
        normalize_devto_totals(article, {"page_views": {}, "reactions": {}}, "now")
    except ValueError:
        pass
    else:
        raise AssertionError("Incomplete analytics must be rejected")


if __name__ == "__main__":
    main()
