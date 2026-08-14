#!/usr/bin/env python3
"""Regression checks for product-agnostic comparison sentiment attribution."""

from build_database_tone import relation_hits


def polarity(sentence: str, database: str) -> int:
    positive, critical = relation_hits(sentence, database)
    return sum(hit["weight"] for hit in positive) - sum(hit["weight"] for hit in critical)


def assert_roles(sentence: str, expected: dict[str, int]) -> None:
    actual = {database: polarity(sentence, database) for database in expected}
    if {database: value > 0 for database, value in actual.items()} != {
        database: value > 0 for database, value in expected.items()
    } or {database: value < 0 for database, value in actual.items()} != {
        database: value < 0 for database, value in expected.items()
    }:
        raise AssertionError(f"{sentence}\nexpected roles: {expected}\nactual roles: {actual}")


def main() -> None:
    products = ["YugabyteDB", "Oracle Database", "PostgreSQL"]
    for offset in range(len(products)):
        subject, advantage, disadvantage = products[offset:] + products[:offset]
        assert_roles(
            f"{subject} brings the advantages of {advantage} to overcome the disadvantages of {disadvantage}.",
            {subject: 1, advantage: 1, disadvantage: -1},
        )
    assert_roles(
        "YugabyteDB combines the advantages of Oracle Database and PostgreSQL.",
        {"YugabyteDB": 1, "Oracle Database": 1, "PostgreSQL": 1},
    )
    assert_roles(
        "Oracle Database is better than PostgreSQL for high availability.",
        {"Oracle Database": 1, "PostgreSQL": -1},
    )
    for offset in range(len(products)):
        claimant, comparison, _ = products[offset:] + products[:offset]
        assert_roles(
            f"{claimant} claims better performance than {comparison}, but its tests lack real-world queries.",
            {claimant: -1, comparison: 0},
        )
    for offset in range(len(products)):
        improving, benchmark, _ = products[offset:] + products[:offset]
        assert_roles(
            f"Last year, {improving} could not substitute {benchmark}'s compound indexes.",
            {improving: 0, benchmark: 1},
        )
        assert_roles(
            f"{improving} now reaches parity with {benchmark}.",
            {improving: 1, benchmark: 1},
        )
        assert_roles(
            f"{improving} offers a {benchmark}-compatible endpoint.",
            {improving: 0, benchmark: 0},
        )
        assert_roles(
            f"{improving}'s new index matches the capabilities of {benchmark}.",
            {improving: 1, benchmark: 1},
        )
    print("Relation sentiment checks passed")


if __name__ == "__main__":
    main()