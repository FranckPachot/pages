#!/usr/bin/env python3
"""Regression checks for publication impact normalization."""

from collect_publication_impact import merge_publications, normalize_devto_totals


def main() -> None:
    article = {
        "id": 4528531,
        "title": "PostgreSQL INCLUDE indexes: what problem are they trying to solve?",
        "canonical_url": "https://dev.to/franckpachot/postgresql-include-indexes-what-problem-are-they-trying-to-solve-4f4n",
        "published_at": "2026-08-31T13:42:16Z",
        "public_reactions_count": 2,
        "comments_count": 0,
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
