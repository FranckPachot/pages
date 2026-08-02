#!/usr/bin/env python3
"""Cache database product logos used by the generated social preview."""

from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ICONIFY_URL = "https://api.iconify.design/{collection}/{name}.svg"
DIRECT_LOGOS = {
    "documentdb.png": "https://documentdb.io/images/DocumentDB%20Logo%20-%20background%20removed.png",
}
LOGOS = {
    "postgresql.svg": [("logos", "postgresql")],
    "yugabytedb.svg": [("devicon", "yugabytedb")],
    "mongodb.svg": [("logos", "mongodb-icon")],
    "aurora.svg": [("logos", "aws-aurora"), ("logos", "aws")],
    "dynamodb.svg": [("logos", "aws-dynamodb"), ("simple-icons", "amazondynamodb")],
    "mysql.svg": [("logos", "mysql-icon")],
    "sql-server.svg": [("devicon", "microsoftsqlserver")],
    "cockroachdb.svg": [("logos", "cockroachdb"), ("simple-icons", "cockroachlabs")],
    "db2.svg": [("carbon", "ibm-db2")],
    "cassandra.svg": [("logos", "cassandra")],
    "azure.svg": [("logos", "microsoft-azure")],
    "sqlite.svg": [("logos", "sqlite")],
}


def fetch_logo(candidates: list[tuple[str, str]]) -> tuple[bytes, str]:
    for collection, name in candidates:
        url = ICONIFY_URL.format(collection=collection, name=name)
        try:
            request = Request(url, headers={"User-Agent": "FranckPachot-pages-builder/1.0"})
            with urlopen(request, timeout=20) as response:
                content = response.read()
            if b"<svg" in content[:500]:
                return content, url
        except HTTPError as error:
            if error.code != 404:
                raise
    raise RuntimeError(f"No SVG logo found for {candidates}")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    output = root / "home" / "database-logos"
    output.mkdir(parents=True, exist_ok=True)
    for filename, source in DIRECT_LOGOS.items():
        request = Request(source, headers={"User-Agent": "FranckPachot-pages-builder/1.0"})
        with urlopen(request, timeout=20) as response:
            (output / filename).write_bytes(response.read())
        print(f"{filename}: {source}")
    for filename, candidates in LOGOS.items():
        content, source = fetch_logo(candidates)
        (output / filename).write_bytes(content)
        print(f"{filename}: {source}")


if __name__ == "__main__":
    main()
