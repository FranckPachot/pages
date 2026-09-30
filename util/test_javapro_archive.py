#!/usr/bin/env python3
"""Regression checks for JAVAPRO publication snapshots."""

import json
import tempfile
from pathlib import Path

from archive_articles import inventory_javapro, javapro_manifest_entry
from build_publication_map import build_catalog


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    detail = {
        "id": 5944,
        "author": 117,
        "date": "2025-12-18T07:00:01",
        "slug": "no-deadlocks-in-mongodb-atomic-documents-and-retries-with-spring-data-mongodb",
        "link": (
            "https://javapro.io/2025/12/18/"
            "no-deadlocks-in-mongodb-atomic-documents-and-retries-with-spring-data-mongodb/"
        ),
        "title": {
            "rendered": (
                "No Deadlocks in MongoDB: Atomic Documents and Retries "
                "with Spring Data MongoDB"
            )
        },
        "content": {"rendered": "<p>MongoDB article</p>"},
    }

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        path = root / "javapro" / "articles" / "5944.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(detail), encoding="utf-8")

        entry = javapro_manifest_entry(root, path, detail, 117)
        assert entry["source"] == "javapro"
        assert entry["source_id"] == "5944"
        assert entry["archive_path"] == "javapro/articles/5944.json"
        assert inventory_javapro(root, 117) == [entry]

        detail["author"] = 42
        try:
            javapro_manifest_entry(root, path, detail, 117)
        except ValueError as error:
            assert "not authored" in str(error)
        else:
            raise AssertionError("Expected an author mismatch to be rejected")

    publications = {
        publication["id"]: publication for publication in build_catalog(ROOT)["publications"]
    }
    assert publications["javapro:5944"]["source"] == "JAVAPRO"
    assert publications["javapro:1191"]["source"] == "JAVAPRO"


if __name__ == "__main__":
    main()
