#!/usr/bin/env python3
"""Build the searchable publication map from archived article snapshots."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SOURCE_NAMES = {
    "dbi-services": "DBI Services",
    "dev.to": "Dev.to",
    "medium": "Medium",
    "microsoft-techcommunity": "Microsoft Tech Community",
    "yugabyte": "Yugabyte",
}

DATABASE_RULES = {
    "Oracle Database": r"\boracle(?: database)?\b|\bora-\d{4,5}\b|\b(?:9i|10g|11g|12c|18c|19c|21c|23c|23ai|26ai)\b",
    "PostgreSQL": r"\bpostgres(?:ql)?\b|\bpg_[a-z0-9_]+\b|\bpsql\b",
    "YugabyteDB": r"\byugabyte(?:db|d)?\b|\byb-[a-z0-9_-]+\b|\bycql\b|\bysql\b",
    "MongoDB": r"\bmongodb\b|\bmongosh\b",
    "Microsoft SQL Server": r"\bsql server\b|\btransact-sql\b|\bt-sql\b",
    "MySQL": r"\bmysql\b|\bmariadb\b",
    "Amazon Aurora": r"\baurora(?: postgresql| mysql| dsql)?\b",
    "Amazon DynamoDB": r"\bdynamodb\b",
    "DocumentDB": r"\bdocumentdb\b",
    "CockroachDB": r"\bcockroachdb\b",
    "Cassandra": r"\bcassandra\b|\bcql\b",
    "SQLite": r"\bsqlite\b",
    "Db2": r"\bdb2\b",
    "SAP HANA": r"\bsap hana\b|\bhana database\b",
}

CATEGORY_RULES = {
    "Query Optimization": r"\boptimizer\b|\bquery planner\b|\bexecution plan\b|\bexplain plan\b|\bcardinality\b|\bcbo\b|\bjoin order\b",
    "Indexing": r"\bindex(?:es|ing)?\b|\bb[+-]?tree\b|\bbitmap scan\b|\bindex scan\b",
    "Performance & Benchmarking": r"\bperformance\b|\bbenchmark\b|\blatency\b|\bthroughput\b|\bpgbench\b|\bslob\b|\bwait event\b|\bload test",
    "High Availability & Replication": r"\bhigh availability\b|\breplication\b|\bdata guard\b|\bstandby\b|\bfailover\b|\bswitchover\b|\bdisaster recovery\b",
    "Distributed Databases": r"\bdistributed\b|\bsharding\b|\bshard\b|\btablet\b|\braft\b|\bconsensus\b|\bgeo-distribut",
    "Transactions & Consistency": r"\btransaction\b|\bacid\b|\bconsistency\b|\bisolation\b|\bserializable\b|\bmvcc\b|\block(?:ing|s)?\b",
    "Internals & Storage": r"\binternals?\b|\bstorage\b|\bwal\b|\bredo\b|\bblock\b|\bbuffer cache\b|\bheap tuple\b|\browid\b",
    "Backup & Recovery": r"\bbackup\b|\brecovery\b|\brestore\b|\brman\b|\barchivelog\b|\bpoint-in-time\b",
    "Migration & Compatibility": r"\bmigrat(?:e|ion|ing)\b|\bcompatib(?:le|ility)\b|\bupgrade\b|\bora2pg\b|\bconversion\b",
    "Cloud & Infrastructure": r"\bcloud\b|\baws\b|\bazure\b|\bgcp\b|\bkubernetes\b|\bdocker\b|\bcontainer\b|\bterraform\b",
    "Security": r"\bsecurity\b|\bprivilege\b|\baudit(?:ing)?\b|\bencrypt(?:ion|ed)?\b|\bauthentication\b|\bauthorization\b|\baccess control\b",
    "Operations & Observability": r"\bmonitor(?:ing)?\b|\bobservability\b|\bmetrics\b|\bstatistics\b|\binstallation\b|\bconfiguration\b|\bpatch(?:ing)?\b",
    "Data Modeling & SQL": r"\bdata model\b|\bschema\b|\bconstraint\b|\bforeign key\b|\bnormal form\b|\brelational algebra\b|\bsql/pgq\b",
    "JSON & Documents": r"\bjsonb?\b|\bbson\b|\bdocument database\b|\bdocument model\b|\bsoda\b",
    "AI & Search": r"\bartificial intelligence\b|\bai functions?\b|\bvector search\b|\bembedding\b|\bdiskann\b|\bbm25\b|\bllm\b|\brag\b",
    "Development & Drivers": r"\bjdbc\b|\bodbc\b|\bdriver\b|\bjava\b|\bpython\b|\bnode\.js\b|\bapplication development\b",
    "Events & Community": r"\bconference\b|\bmeetup\b|\bwebinar\b|\bkeynote\b|\bdoag\b|\bukoug\b|\bcommunity\b",
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav", "footer"}:
            self.ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer"} and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


class DescriptionExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta" or self.description:
            return
        attributes = {name.casefold(): value or "" for name, value in attrs}
        if attributes.get("name", "").casefold() == "description":
            self.description = normalize_text(attributes.get("content", ""))


def html_text(value: str) -> str:
    extractor = TextExtractor()
    extractor.feed(value)
    return normalize_text(" ".join(extractor.parts))


def html_description(value: str) -> str:
    extractor = DescriptionExtractor()
    extractor.feed(value)
    return extractor.description


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def load_snapshot(root: Path, article: dict[str, Any]) -> tuple[str, str]:
    path = root / article["archive_path"]
    source = article["source"]
    if source in {"dbi-services", "medium", "microsoft-techcommunity"}:
        document = path.read_text(encoding="utf-8", errors="replace")
        return html_text(document), html_description(document)

    value = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if source == "dev.to":
        body = value.get("body_markdown") or html_text(value.get("body_html", ""))
        return normalize_text(body), normalize_text(value.get("description", ""))
    if source == "yugabyte":
        body = html_text(value.get("content", {}).get("rendered", ""))
        description = value.get("yoast_head_json", {}).get("description", "")
        return body, normalize_text(description)
    return "", ""


def first_match(pattern: str, value: str) -> str:
    match = re.search(pattern, value, flags=re.IGNORECASE | re.DOTALL)
    return normalize_text(match.group(1)) if match else ""


def unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def infer_databases(signal: str) -> list[str]:
    return [name for name, pattern in DATABASE_RULES.items() if re.search(pattern, signal, re.IGNORECASE)]


def infer_categories(signal: str) -> list[str]:
    categories = [
        name for name, pattern in CATEGORY_RULES.items() if re.search(pattern, signal, re.IGNORECASE)
    ]
    return categories or ["General Database"]


def infer_versions(signal: str, databases: list[str]) -> list[str]:
    versions: list[str] = []
    oracle_aliases = {
        "9i": "9i",
        "10g": "10g",
        "11g": "11g",
        "12c": "12c",
        "18c": "18c",
        "19c": "19c",
        "21c": "21c",
        "23c": "23c",
        "23ai": "23ai",
        "26ai": "26ai",
    }
    if "Oracle Database" in databases:
        for match in re.findall(r"\b(9i|10g|11g|12c|18c|19c|21c|23c|23ai|26ai)\b", signal, re.I):
            versions.append(f"Oracle {oracle_aliases[match.casefold()]}")
        for match in re.findall(r"\b(?:Oracle(?: Database)?\s+)?((?:9|10|11|12|18|19|21|23|26)\.\d+(?:\.\d+){0,2})\b", signal, re.I):
            versions.append(f"Oracle {match}")

    version_patterns = {
        "PostgreSQL": r"\b(?:PostgreSQL|Postgres|PG)\s+(?:version\s+|v)?(\d{1,2}(?:\.\d+)?)\b",
        "YugabyteDB": r"\b(?:YugabyteDB|YB)\s+(?:version\s+|v)?(\d+\.\d+(?:\.\d+)?)\b",
        "MongoDB": r"\bMongoDB\s+(?:version\s+|v)?(\d+\.\d+(?:\.\d+)?)\b",
        "MySQL": r"\bMySQL\s+(?:version\s+|v)?(\d+\.\d+(?:\.\d+)?)\b",
        "Microsoft SQL Server": r"\bSQL Server\s+(20\d{2})\b",
    }
    for database, pattern in version_patterns.items():
        if database in databases:
            versions.extend(f"{database} {match}" for match in re.findall(pattern, signal, re.I))
    return unique_strings(versions)


def build_catalog(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "archive-manifest.json").read_text(encoding="utf-8"))
    publications = []
    for article in manifest["articles"]:
        body, description = load_snapshot(root, article)
        tags = unique_strings([normalize_text(tag) for tag in article.get("tags", [])])
        title = normalize_text(article["title"])
        signal = " ".join([title, " ".join(tags), body[:1800]])
        databases = infer_databases(signal)
        versions = infer_versions(signal, databases)
        categories = infer_categories(signal)
        summary = description or body[:320]
        date = article["published_at"][:10]
        archive_url = "../" + article["archive_path"]
        read_url = archive_url if article["source"] in {"dbi-services", "medium"} else article["canonical_url"]
        search_text = normalize_text(
            " ".join([title, summary, " ".join(tags + categories + databases + versions), body[:3500]])
        ).casefold()
        publications.append(
            {
                "id": f"{article['source']}:{article['source_id']}",
                "title": title,
                "date": date,
                "year": int(date[:4]),
                "source": SOURCE_NAMES.get(article["source"], article["source"]),
                "source_key": article["source"],
                "read_url": read_url,
                "archive_url": archive_url,
                "canonical_url": article["canonical_url"],
                "summary": summary[:360],
                "tags": tags,
                "categories": categories,
                "databases": databases or ["Database agnostic"],
                "versions": versions,
                "search_text": search_text,
            }
        )

    database_counts = Counter(value for item in publications for value in item["databases"])
    category_counts = Counter(value for item in publications for value in item["categories"])
    version_counts = Counter(value for item in publications for value in item["versions"])
    tag_counts = Counter(value for item in publications for value in item["tags"])
    return {
        "generated_from_schema": manifest["schema_version"],
        "publication_count": len(publications),
        "year_min": min(item["year"] for item in publications),
        "year_max": max(item["year"] for item in publications),
        "source_counts": manifest["sources"],
        "database_counts": dict(database_counts.most_common()),
        "category_counts": dict(category_counts.most_common()),
        "version_counts": dict(version_counts.most_common()),
        "tag_counts": dict(tag_counts.most_common()),
        "publications": publications,
    }


def write_catalog(path: Path, catalog: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(catalog, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(f"window.PUBLICATION_CATALOG={payload};\n", encoding="utf-8")
    os.replace(temporary_path, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / "home" / "publications.js"
    catalog = build_catalog(root)
    write_catalog(output, catalog)
    print(
        f"Wrote {output} with {catalog['publication_count']} publications, "
        f"{len(catalog['database_counts'])} database facets, and "
        f"{len(catalog['category_counts'])} categories"
    )


if __name__ == "__main__":
    main()