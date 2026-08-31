#!/usr/bin/env python3
"""Regression checks for database-version attribution in the publication map."""

from pathlib import Path

from build_publication_map import build_catalog, infer_versions


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

    oracle_versions = infer_versions(
        "Oracle 8.1.7 preceded 8i, while Oracle Database 19.3 belongs to the 19c family.",
        ["Oracle Database"],
    )
    assert oracle_versions == ["Oracle 8i", "Oracle 19c", "Oracle 8.1.7", "Oracle 19.3"]

    publications = {
        publication["id"]: publication for publication in build_catalog(ROOT)["publications"]
    }
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