#!/usr/bin/env python3
"""Regression checks for database-version attribution in the publication map."""

import json
import tempfile
from pathlib import Path

from build_publication_map import build_catalog, infer_databases, infer_versions


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    mixed_products = (
        "Here is output in PostgreSQL 8.4 and 9.3. Index-only scans were introduced "
        "in 9.2, and INCLUDE came later in 11. Oracle users have built covering indexes "
        "for decades."
    )
    versions = infer_versions(mixed_products, ["PostgreSQL", "Oracle Database"])
    assert versions == [
        "PostgreSQL 8.4",
        "PostgreSQL 9.3",
        "PostgreSQL 9.2",
        "PostgreSQL 11",
    ]
    assert "Oracle 9.2" not in versions
    assert "Oracle 9.3" not in versions

    assert infer_versions(
        "There is no other lock situation in Postgres at least since version 9.3.",
        ["PostgreSQL", "Oracle Database"],
    ) == ["PostgreSQL 9.3"]
    assert infer_versions(
        "Oracle 11g, MySQL 5.6, Postgres 9.6 and 9.3, SQLite.",
        ["Oracle Database", "MySQL", "PostgreSQL", "SQLite"],
    ) == ["Oracle 11g", "PostgreSQL 9.6", "PostgreSQL 9.3", "MySQL 5.6"]
    for signal in (
        "Azure Database for PostgreSQL Flexible Server",
        "Azure PostgreSQL",
        "Azure Flexible Server",
        "az postgres flexible-server parameter set",
    ):
        assert {"Azure Database for PostgreSQL", "PostgreSQL"}.issubset(
            infer_databases(signal)
        )
    assert {"Azure HorizonDB", "PostgreSQL"}.issubset(
        infer_databases("Azure HorizonDB")
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        prefix = "SQL walkthrough. " * 180
        articles = []
        for source_id, title, tags, body in (
            (
                "late-azure-postgresql",
                "PostgreSQL and DuckDB data lake",
                ["azure"],
                prefix + "This plan runs on Azure Database for PostgreSQL.",
            ),
            (
                "azure-blob-only",
                "PostgreSQL and DuckDB data lake",
                ["azure"],
                prefix + "Azure Blob Storage is read from PostgreSQL.",
            ),
            (
                "horizondb-comparison",
                "Azure HorizonDB and DuckDB",
                ["azure"],
                prefix + "This feature is not available in Azure Database for PostgreSQL.",
            ),
            (
                "untagged-postgresql",
                "PostgreSQL query planning",
                [],
                prefix + "Microsoft supports Azure Database for PostgreSQL migrations.",
            ),
        ):
            snapshot = root / f"{source_id}.json"
            snapshot.write_text(json.dumps({"body_markdown": body}), encoding="utf-8")
            articles.append(
                {
                    "source": "dev.to",
                    "source_id": source_id,
                    "title": title,
                    "published_at": "2026-10-15T07:59:08Z",
                    "canonical_url": f"https://dev.to/example/{source_id}",
                    "archive_path": snapshot.name,
                    "tags": tags,
                }
            )
        (root / "archive-manifest.json").write_text(
            json.dumps({"schema_version": 1, "articles": articles}), encoding="utf-8"
        )
        fixtures = {
            publication["id"]: publication for publication in build_catalog(root)["publications"]
        }
        assert fixtures["dev.to:late-azure-postgresql"]["databases"] == [
            "Azure Database for PostgreSQL",
            "PostgreSQL",
            "DuckDB",
        ]
        for source_id in ("azure-blob-only", "horizondb-comparison", "untagged-postgresql"):
            assert "Azure Database for PostgreSQL" not in fixtures[f"dev.to:{source_id}"]["databases"]

    oracle_versions = infer_versions(
        "Oracle 8.1.7 preceded 8i, while Oracle Database 19.3 belongs to the 19c family.",
        ["Oracle Database"],
    )
    assert oracle_versions == ["Oracle 8i", "Oracle 19c", "Oracle 8.1.7", "Oracle 19.3"]

    publications = {
        publication["id"]: publication for publication in build_catalog(ROOT)["publications"]
    }
    assert {"Amazon Aurora", "DuckDB", "PostgreSQL"}.issubset(
        publications["dev.to:4803170"]["databases"]
    )
    assert {"Azure Database for PostgreSQL", "DuckDB", "PostgreSQL"}.issubset(
        publications["dev.to:4812637"]["databases"]
    )
    assert {"Azure Database for PostgreSQL", "DuckDB", "PostgreSQL"}.issubset(
        publications["dev.to:4820013"]["databases"]
    )
    assert "Azure Database for PostgreSQL" not in publications["dev.to:3999543"]["databases"]
    assert {"Azure HorizonDB", "PostgreSQL"}.issubset(
        publications["microsoft-techcommunity:4540160"]["databases"]
    )
    assert {"Azure HorizonDB", "PostgreSQL"}.issubset(
        publications["microsoft-techcommunity:4544728"]["databases"]
    )
    assert {"Azure HorizonDB", "PostgreSQL"}.issubset(
        publications["dev.to:4190390"]["databases"]
    )
    assert {
        "Azure Database for PostgreSQL",
        "Azure HorizonDB",
        "PostgreSQL",
    }.issubset(publications["linkedin:q4ede"]["databases"])
    include_versions = publications["dev.to:4528531"]["versions"]
    assert include_versions == [
        "PostgreSQL 11",
        "PostgreSQL 8.4",
        "PostgreSQL 9.3",
        "PostgreSQL 9.2",
    ], include_versions
    cern_versions = publications["cern:143"]["versions"]
    assert "Oracle 9.3" not in cern_versions, cern_versions
    sql_fiddle_versions = publications["dbi-services:testing-oracle-sql-online"]["versions"]
    assert {
        "Oracle 11g",
        "PostgreSQL 9.6",
        "PostgreSQL 9.3",
        "MySQL 5.6",
        "Microsoft SQL Server 2014",
    }.issubset(sql_fiddle_versions), sql_fiddle_versions
    assert "Oracle 9.6" not in sql_fiddle_versions, sql_fiddle_versions
    assert "Oracle 9.3" not in sql_fiddle_versions, sql_fiddle_versions


if __name__ == "__main__":
    main()