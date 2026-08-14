#!/usr/bin/env python3
"""Build the searchable publication map from archived article snapshots."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote

from google_analytics import install_google_tags


SITE_URL = "https://franckpachot.github.io/pages/"


SOURCE_NAMES = {
    "cern": "CERN",
    "dbi-services": "dbi services",
    "developpez": "Developpez.com",
    "dev.to": "Dev.to",
    "linkedin": "LinkedIn",
    "medium": "Medium",
    "microsoft-techcommunity": "Microsoft Tech Community",
    "oracle-scene": "Oracle Scene",
    "slideshare": "SlideShare",
    "soug": "SOUG",
    "yugabyte": "Yugabyte",
}

EMPLOYMENT_PERIODS = [
    {"key": "microsoft-2026", "company": "Microsoft", "range": "Jun 2026-Present", "start": "2026-06-01"},
    {"key": "mongodb-2025", "company": "MongoDB", "range": "Feb 2025-May 2026", "start": "2025-02-06"},
    {"key": "yugabyte-2021", "company": "Yugabyte", "range": "Jul 2021-Feb 2025", "start": "2021-07-01"},
    {"key": "dbi-services-2020", "company": "dbi services", "range": "Feb 2020-Jun 2021", "start": "2020-02-01"},
    {"key": "cern-2018", "company": "CERN", "range": "Sep 2018-Feb 2020", "start": "2018-09-01"},
    {"key": "dbi-services-2014", "company": "dbi services", "range": "2014-Sep 2018", "start": "2014-01-01"},
    {"key": "trivadis-2010", "company": "Trivadis AG", "range": "Dec 2010-Nov 2013", "start": "2010-12-01"},
]

DATABASE_RULES = {
    "Azure HorizonDB": r"\b(?:microsoft\s+)?(?:azure\s+)?horizondb\b",
    "Oracle Database": r"\boracle(?: database|text)?\b|\bora-\d{4,5}\b|\b(?:9i|10g|11g|12c|18c|19c|21c|23c|23ai|26ai)(?:r[12])?\b|\b(?:v|gv|x)\$[a-z0-9_$#]+\b|\b(?:dba|cdb)_[a-z0-9_$#]+\b|\b(?:dbms|utl|owa|ctx|sdo)_[a-z0-9_$#]+\b|\b(?:sql\*plus|sqlplus|sqlcl|rman|data\s*guard|golden\s*gate|exadata|awr|statspack|pl/sql|varchar2|sysdate|systimestamp|rownum|connect by|match_recognize|pluggable database|flashback table|asm iostats)\b|\basm_[a-z0-9_$#]+\b|\b(?:cdb|pdb)\$root\b",
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
DATABASE_COLORS = {
    "Oracle Database": "#c74634",
    "PostgreSQL": "#336791",
    "YugabyteDB": "#ff5f3b",
    "MongoDB": "#47a248",
    "Amazon Aurora": "#8c4fff",
    "Amazon DynamoDB": "#4053d6",
    "MySQL": "#4479a1",
    "Microsoft SQL Server": "#cc2927",
    "DocumentDB": "#c925d1",
    "CockroachDB": "#6933ff",
    "Db2": "#009a2b",
    "Cassandra": "#1287b1",
    "Azure HorizonDB": "#0078d4",
    "SQLite": "#003b57",
    "Database agnostic": "#aeb8b4",
}


def load_ai_descriptions(root: Path) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    description_dir = root / "util" / "publication_descriptions"
    for path in sorted(description_dir.glob("*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        if "descriptions" in batch:
            for source, source_descriptions in batch["descriptions"].items():
                for source_id, description in source_descriptions.items():
                    descriptions[f"{source}:{source_id}"] = description
        else:
            descriptions.update(batch)
    return descriptions

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
    if source in {"oracle-scene", "soug"}:
        description = normalize_text(article.get("description", ""))
        signal = " ".join([article["title"], description, " ".join(article.get("tags", []))])
        return normalize_text(signal), description
    if source in {"developpez", "medium", "microsoft-techcommunity", "slideshare"} or (
        source == "dbi-services" and path.suffix.casefold() == ".html"
    ):
        document = path.read_text(encoding="utf-8", errors="replace")
        return html_text(document), html_description(document)

    value = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if source == "dbi-services":
        body = html_text(value.get("content", {}).get("rendered", ""))
        return body, ""
    if source == "dev.to":
        body = value.get("body_markdown") or html_text(value.get("body_html", ""))
        return normalize_text(body), normalize_text(value.get("description", ""))
    if source == "yugabyte":
        body = html_text(value.get("content", {}).get("rendered", ""))
        description = value.get("yoast_head_json", {}).get("description", "")
        return body, normalize_text(description)
    if source == "cern":
        body = html_text(value.get("attributes", {}).get("body", {}).get("processed", ""))
        return body, ""
    if source == "linkedin":
        return html_text(value.get("body_html", "")), ""
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


def employment_period(date: str) -> dict[str, str]:
    for period in EMPLOYMENT_PERIODS:
        if date >= period["start"]:
            return period
    raise ValueError(f"No employment period configured for publication date {date}")


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


def publication_urls(root: Path, article: dict[str, Any]) -> tuple[str, str]:
    archive_url = article["archive_path"]
    if article["source"] in {"oracle-scene", "soug"}:
        return archive_url, article["canonical_url"]
    if article["source"] == "dbi-services" and archive_url.endswith(".json"):
        legacy_url = f"2013-2018/{article['source_id']}/index.html"
        if (root / legacy_url).is_file():
            return legacy_url, ""
        rendered_url = f"dbi-services/rendered/{article['source_id']}/index.html"
        if (root / rendered_url).is_file():
            return rendered_url, article["canonical_url"]
        return article["canonical_url"], ""

    read_url = archive_url if article["source"] == "medium" else article["canonical_url"]
    snapshot_url = archive_url if archive_url.endswith((".html", "/index.html")) and read_url != archive_url else ""
    return read_url, snapshot_url


def build_catalog(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "archive-manifest.json").read_text(encoding="utf-8"))
    ai_descriptions = load_ai_descriptions(root)
    publications = []
    linkedin_canonicals = {
        article["canonical_url"].rstrip("/")
        for article in manifest["articles"]
        if article["source"] == "linkedin"
    }
    for article in manifest["articles"]:
        if (
            article["source"] != "linkedin"
            and article["canonical_url"].rstrip("/") in linkedin_canonicals
        ):
            continue
        body, description = load_snapshot(root, article)
        tags = unique_strings([normalize_text(tag) for tag in article.get("tags", [])])
        title = normalize_text(article["title"])
        signal = " ".join([title, " ".join(tags), body[:1800]])
        databases = infer_databases(signal)
        horizon_signal = " ".join([title, " ".join(tags), description])
        if "Azure HorizonDB" in databases and not re.search(DATABASE_RULES["Azure HorizonDB"], horizon_signal, re.IGNORECASE):
            databases.remove("Azure HorizonDB")
        versions = infer_versions(signal, databases)
        categories = infer_categories(signal)
        article_id = f"{article['source']}:{article['source_id']}"
        summary = ai_descriptions.get(article_id) or description or body[:320]
        date = article["published_at"][:10]
        employment = employment_period(date)
        archive_url = article["archive_path"]
        read_url, snapshot_url = publication_urls(root, article)
        search_text = normalize_text(
            " ".join([title, summary, " ".join(tags + categories + databases + versions), body[:3500]])
        ).casefold()
        publications.append(
            {
                "id": article_id,
                "title": title,
                "date": date,
                "year": int(date[:4]),
                "employment_period": employment["key"],
                "source": SOURCE_NAMES.get(article["source"], article["source"]),
                "source_key": article["source"],
                "read_url": read_url,
                "archive_url": archive_url,
                "snapshot_url": snapshot_url,
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
    employment_counts = Counter(item["employment_period"] for item in publications)
    return {
        "generated_from_schema": manifest["schema_version"],
        "publication_count": len(publications),
        "year_min": min(item["year"] for item in publications),
        "year_max": max(item["year"] for item in publications),
        "source_counts": dict(Counter(item["source_key"] for item in publications)),
        "employment_periods": [
            {**period, "count": employment_counts[period["key"]]}
            for period in EMPLOYMENT_PERIODS
            if employment_counts[period["key"]]
        ],
        "database_counts": dict(database_counts.most_common()),
        "database_colors": DATABASE_COLORS,
        "category_counts": dict(category_counts.most_common()),
        "version_counts": dict(version_counts.most_common()),
        "tag_counts": dict(tag_counts.most_common()),
        "publications": publications,
    }


def write_catalog(path: Path, catalog: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(catalog, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    content = f"window.PUBLICATION_CATALOG={payload};\n"
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(content, encoding="utf-8")
    os.replace(temporary_path, path)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


def publication_markup(publication: dict[str, Any]) -> str:
    title = html.escape(publication["title"])
    summary = html.escape(publication["summary"])
    url = html.escape(publication["read_url"], quote=True)
    external = ' target="_blank" rel="noopener"' if publication["read_url"].startswith("http") else ""
    summary_markup = f'\n          <p class="publication__summary">{summary}</p>' if summary else ""
    source_key = html.escape(publication["source_key"], quote=True)
    source = html.escape(publication["source"])
    snapshot_markup = ""
    if publication["snapshot_url"]:
        snapshot_url = html.escape(publication["snapshot_url"], quote=True)
        snapshot_markup = f'<a class="snapshot-link" href="{snapshot_url}">Archived copy ↗</a>'
    return (
        '      <article class="publication">\n'
        f'        <time class="publication__date" datetime="{publication["date"]}">{publication["date"]}</time>\n'
        '        <div>\n'
        f'          <a class="publication__title" href="{url}"{external}>{title}</a>{summary_markup}\n'
        '        </div>\n'
        f'        <div class="publication__meta"><span class="badge badge--source"><span class="source-logo source-logo--{source_key}" aria-hidden="true"></span>{source}</span>{snapshot_markup}</div>\n'
        '      </article>'
    )


def replace_generated_block(document: str, name: str, content: str) -> str:
    pattern = rf"(?s)(<!-- GENERATED_{name}_START -->).*?(<!-- GENERATED_{name}_END -->)"
    updated, count = re.subn(pattern, lambda match: f"{match.group(1)}\n{content}\n        {match.group(2)}", document)
    if count != 1:
        raise ValueError(f"Expected one generated {name} block, found {count}")
    return updated


def write_root_index(path: Path, catalog: dict[str, Any], catalog_version: str) -> None:
    document = path.read_text(encoding="utf-8")
    app_version = hashlib.sha256((path.parent / "home" / "app.js").read_bytes()).hexdigest()[:12]
    style_version = hashlib.sha256((path.parent / "home" / "style.css").read_bytes()).hexdigest()[:12]
    minibook_count = sum(1 for index_path in (path.parent / "minibook").glob("*/index.html"))
    recent = sorted(catalog["publications"], key=lambda publication: publication["date"], reverse=True)[:80]
    results = "\n".join(publication_markup(publication) for publication in recent)
    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Recent database articles by Franck Pachot",
        "numberOfItems": len(catalog["publications"]),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "url": publication["canonical_url"],
                "name": publication["title"],
            }
            for position, publication in enumerate(recent[:20], 1)
        ],
    }
    structured_data = f'  <script type="application/ld+json">{json.dumps(item_list, ensure_ascii=False, separators=(",", ":"))}</script>'
    document = replace_generated_block(document, "RESULTS", results)
    document = replace_generated_block(document, "ITEM_LIST", structured_data)
    document, count = re.subn(
        r'(<script\s+src="home/publications\.js)(?:\?v=[^"]*)?("></script>)',
        lambda match: f"{match.group(1)}?v={catalog_version}{match.group(2)}",
        document,
    )
    if count != 1:
        raise ValueError(f"Expected one publications.js script, found {count}")
    document, count = re.subn(
        r'(<script\s+src="home/app\.js)(?:\?v=[^"]*)?("[^>]*></script>)',
        lambda match: f"{match.group(1)}?v={app_version}{match.group(2)}",
        document,
    )
    if count != 1:
        raise ValueError(f"Expected one app.js script, found {count}")
    document, count = re.subn(
        r'(<link\s+rel="stylesheet"\s+href="home/style\.css)(?:\?v=[^"]*)?("[^>]*>)',
        lambda match: f"{match.group(1)}?v={style_version}{match.group(2)}",
        document,
    )
    if count != 1:
        raise ValueError(f"Expected one style.css link, found {count}")
    document, count = re.subn(
        r"(https://franckpachot\.github\.io/pages/home/social-card\.png)(?:\?v=[^\"']*)?",
        rf"\g<1>?v={catalog_version}",
        document,
    )
    if count < 2:
        raise ValueError(f"Expected at least two social-card URLs, found {count}")
    document, count = re.subn(
        r"(Database field guides · )\d+( volumes)",
        rf"\g<1>{minibook_count}\2",
        document,
    )
    if count != 1:
        raise ValueError(f"Expected one minibook volume count, found {count}")
    path.write_text(document, encoding="utf-8")


def write_social_preview(root: Path, catalog: dict[str, Any]) -> None:
    database_counts = {
        name: count
        for name, count in catalog["database_counts"].items()
        if name != "Database agnostic"
    }
    chart_data = list(database_counts.items())
    all_total = sum(database_counts.values())
    brand_colors = DATABASE_COLORS
    logo_files = {
        "Oracle Database": "oracle-o.svg",
        "PostgreSQL": "postgresql.svg",
        "YugabyteDB": "yugabytedb.svg",
        "MongoDB": "mongodb.svg",
        "Amazon Aurora": "aurora.svg",
        "Amazon DynamoDB": "dynamodb.svg",
        "MySQL": "mysql.svg",
        "Microsoft SQL Server": "sql-server.svg",
        "DocumentDB": "documentdb.png",
        "CockroachDB": "cockroachdb.svg",
        "Db2": "db2.png",
        "Cassandra": "cassandra.svg",
        "Azure HorizonDB": "azure.svg",
        "SQLite": "sqlite.svg",
    }
    initials = {
        "Oracle Database": "O", "PostgreSQL": "PG", "YugabyteDB": "YB", "MongoDB": "M",
        "Amazon Aurora": "A", "Amazon DynamoDB": "D", "MySQL": "MY", "Microsoft SQL Server": "MS",
        "DocumentDB": "D", "CockroachDB": "CR", "Db2": "2", "Cassandra": "C",
        "Azure HorizonDB": "H", "SQLite": "SQ",
    }
    circumference = 2 * math.pi * 126
    offset = 0.0
    arcs = []
    legend = []
    for position, (name, count) in enumerate(chart_data):
        color = brand_colors[name]
        length = circumference * count / all_total
        arcs.append(
            f'<circle cx="865" cy="230" r="126" fill="none" stroke="{color}" stroke-width="48" '
            f'stroke-dasharray="{length:.2f} {circumference - length:.2f}" stroke-dashoffset="{-offset:.2f}"/>'
        )
        offset += length
        column = position % 7
        row = position // 7
        legend_x = 638 + column * 74
        legend_y = 410 + row * 74
        mark = initials.get(name, name[:2].upper())
        logo_path = root / "home" / "database-logos" / logo_files[name]
        if logo_path.exists():
            logo = (
                f'<image href="database-logos/{logo_files[name]}" x="{legend_x + 14}" y="{legend_y + 7}" '
                'width="42" height="36" preserveAspectRatio="xMidYMid meet"/>'
            )
        else:
            logo = (
                f'<g class="logo-mark"><rect x="{legend_x + 17}" y="{legend_y + 8}" width="36" height="34" fill="{color}"/>'
                f'<text x="{legend_x + 35}" y="{legend_y + 30}" text-anchor="middle">{mark}</text></g>'
            )
        legend.append(
            f'<g class="logo-tile"><title>{html.escape(name)}: {count:,} posts</title>'
            f'<rect x="{legend_x}" y="{legend_y}" width="70" height="70" fill="#fff" fill-opacity=".78" stroke="{color}" stroke-width="2.5"/>'
            + logo
            + f'<text x="{legend_x + 35}" y="{legend_y + 61}" text-anchor="middle" class="tile-count">{count:,}</text></g>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#d9dfdc" stroke-width="1" opacity=".45"/></pattern>
    <style>
      text {{ font-family: "Arial", "Helvetica", sans-serif; fill: #182522; }}
      .eyebrow {{ font-size: 18px; font-weight: 700; letter-spacing: 3px; fill: #24706b; }}
      .title {{ font-family: "Georgia", serif; font-size: 56px; font-weight: 700; }}
      .count {{ font-size: 24px; font-weight: 700; fill: #c74634; }}
      .word {{ font-weight: 700; fill: #3e514d; }}
    .tile-count {{ font-size: 13px; font-weight: 800; fill: #273a36; }}
    .logo-mark text {{ font-size: 9px; font-weight: 800; fill: white; }}
      .chart-label {{ font-size: 15px; font-weight: 700; letter-spacing: 1px; fill: #65736f; }}
      .chart-total {{ font-family: "Georgia", serif; font-size: 44px; font-weight: 700; }}
      .chart-note {{ font-size: 13px; fill: #65736f; }}
    </style>
  </defs>
  <rect width="1200" height="630" fill="#f4f2ec"/>
  <rect width="1200" height="630" fill="url(#grid)"/>
  <rect x="0" y="0" width="18" height="630" fill="#24706b"/>
    <text x="70" y="76" class="eyebrow">FRANCK PACHOT · DATABASE BLOG ARCHIVE</text>
    <text x="70" y="150" class="title">Database blog posts</text>
    <text x="70" y="205" class="title">by Franck Pachot</text>
    <text x="70" y="252" class="count">{catalog['publication_count']:,} posts · over 12 years</text>
  <text x="70" y="325" class="word" font-size="32">INDEXES</text>
  <text x="285" y="325" class="word" font-size="20">QUERY PLANS</text>
  <text x="90" y="368" class="word" font-size="22">MVCC</text>
  <text x="190" y="368" class="word" font-size="29">DISTRIBUTED SQL</text>
  <text x="70" y="412" class="word" font-size="19">REPLICATION</text>
  <text x="230" y="412" class="word" font-size="24">TRANSACTIONS</text>
  <text x="86" y="453" class="word" font-size="27">STORAGE</text>
  <text x="230" y="453" class="word" font-size="18">OBSERVABILITY</text>
  <text x="70" y="492" class="word" font-size="18">MIGRATION</text>
  <text x="190" y="492" class="word" font-size="24">VECTOR SEARCH</text>
  <text x="92" y="530" class="word" font-size="20">JSON</text>
  <text x="160" y="530" class="word" font-size="28">PERFORMANCE</text>
    <text x="865" y="67" text-anchor="middle" class="chart-label">POSTS BY DATABASE · ALL TAGS</text>
    <g transform="rotate(-90 865 230)">{''.join(arcs)}</g>
    <circle cx="865" cy="230" r="102" fill="#f4f2ec"/>
    <text x="865" y="222" text-anchor="middle" class="chart-total">{all_total:,}</text>
    <text x="865" y="248" text-anchor="middle" class="chart-note">database mentions</text>
    <text x="865" y="271" text-anchor="middle" class="chart-note">posts may have several tags</text>
  {''.join(legend)}
</svg>'''
    svg_path = root / "home" / "social-card.svg"
    png_path = root / "home" / "social-card.png"
    svg_path.write_text(svg, encoding="utf-8")
    browser_candidates = [
        shutil.which("msedge"),
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    browser = next((Path(candidate) for candidate in browser_candidates if candidate and Path(candidate).exists()), None)
    if browser:
        subprocess.run(
            [
                str(browser),
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                "--window-size=1200,630",
                f"--screenshot={png_path}",
                svg_path.as_uri(),
            ],
            check=True,
            capture_output=True,
        )
    elif not png_path.exists():
        raise RuntimeError("Chrome or Edge is required to create home/social-card.png")


def write_sitemap(path: Path, catalog: dict[str, Any], root: Path) -> None:
    local_pages = [
        publication for publication in catalog["publications"]
        if publication["source_key"] in {"dbi-services", "medium"}
    ]
    minibook_pages = [
        f"{index_path.parent.relative_to(root).as_posix()}/"
        for index_path in sorted((root / "minibook").glob("*/index.html"))
    ]
    static_pages = ["", "minibook/", *minibook_pages]
    entries = [f"  <url><loc>{SITE_URL}{page}</loc></url>" for page in static_pages]
    for publication in local_pages:
        url = SITE_URL + quote(publication["archive_url"], safe="/-._~")
        entries.append(f"  <url><loc>{html.escape(url)}</loc><lastmod>{publication['date']}</lastmod></url>")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(entries) + "\n</urlset>\n"
    path.write_text(sitemap, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument(
        "--skip-google-analytics",
        action="store_true",
        help="Do not add Google Analytics tags to archived HTML pages",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / "home" / "publications.js"
    catalog = build_catalog(root)
    catalog_version = write_catalog(output, catalog)
    write_root_index(root / "index.html", catalog, catalog_version)
    write_social_preview(root, catalog)
    write_sitemap(root / "sitemap.xml", catalog, root)
    write_sitemap(root / "home" / "sitemap.xml", catalog, root)
    print(
        f"Wrote {output} with {catalog['publication_count']} publications, "
        f"{len(catalog['database_counts'])} database facets, and "
        f"{len(catalog['category_counts'])} categories"
    )
    if not args.skip_google_analytics:
        analytics_changed, analytics_tagged = install_google_tags(root)
        print(f"Google tag: updated {analytics_changed} pages; {analytics_tagged} pages tagged")


if __name__ == "__main__":
    main()