#!/usr/bin/env python3
"""Generate the source-grounded database experience reference for agents."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from build_minibooks import BOOKS, TECHNICAL_GUIDES, resolve_sources
from build_publication_map import build_catalog


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "db-skills.md"


def markdown_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def code_fence(value: str) -> str:
    fence = "```"
    while fence in value:
        fence += "`"
    return f"{fence}sql\n{value.rstrip()}\n{fence}"


def source_label(publication: dict[str, Any]) -> str:
    databases = ", ".join(publication["databases"])
    categories = ", ".join(publication["categories"])
    return f"{publication['date']} | {publication['source']} | {databases} | {categories}"


def publication_link(publication: dict[str, Any]) -> str:
    title = markdown_text(publication["title"])
    return f"[{title}]({publication['canonical_url']})"


def render_experience_contract(lines: list[str]) -> None:
    lines.extend(
        [
            "## How an agent must use this knowledge",
            "",
            "This is an evidence map and field manual, not an authority that overrides current product documentation or observed behavior. The publications record experiments and operational experience across database products and versions. Apply them with these rules:",
            "",
            "1. Start from the invariant, workload, failure model, and database version. Do not begin from a feature name or a preferred product.",
            "2. Separate logical semantics from physical implementation. Similar SQL syntax does not imply identical MVCC, locking, indexing, durability, or distributed execution costs.",
            "3. Treat every plan as a forecast and every benchmark as conditional evidence. Verify estimates, actual rows, loops, buffers, waits, RPCs, log volume, and client fetch behavior on the target system.",
            "4. Distinguish correctness controls from performance aids. Constraints, transaction boundaries, durability settings, and replication acknowledgement define guarantees; indexes and caches change the cost of enforcing them.",
            "5. Preserve product and version boundaries. A finding about Oracle, PostgreSQL, YugabyteDB, MongoDB, or a cloud service is not universal unless independently demonstrated.",
            "6. Prefer a two-session or failure-injection experiment for concurrency, isolation, replication, and recovery claims. A single successful execution proves little about races or failure behavior.",
            "7. For consequential advice, open the cited publication snapshot, confirm its assumptions and date, then check current vendor documentation and reproduce the observation.",
            "8. State uncertainty. If the evidence is indirect, version-specific, or inferred from implementation details, say so and propose the cheapest discriminating test.",
            "",
            "### Investigation loop",
            "",
            "1. Capture the exact statement or operation, parameters, schema, data distribution, version, settings, topology, and observed symptom.",
            "2. Name one falsifiable hypothesis at the lowest layer that explains the evidence.",
            "3. Choose one measurement that can disprove it before changing configuration.",
            "4. Change one input at a time and compare the same counters under a representative workload.",
            "5. Record the guarantee gained or lost, not only the latency change.",
            "6. Retest under concurrency, restart, failover, or skew when those conditions are part of the claim.",
            "",
        ]
    )


def render_book(
    lines: list[str],
    book: dict[str, Any],
    publications_by_id: dict[str, dict[str, Any]],
    publications_by_canonical: dict[str, dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> None:
    lines.extend(
        [
            f"## {book['number']}. {book['title']}",
            "",
            f"**{book['subtitle']}**",
            "",
            book["description"],
            "",
        ]
    )

    for chapter_title, lead, points in book["chapters"]:
        lines.extend([f"### {chapter_title}", "", lead, ""])
        lines.extend(f"- {point}" for point in points)
        lines.append("")

    guides = TECHNICAL_GUIDES.get(book["slug"], [])
    if not guides:
        raise ValueError(f"No technical guides for {book['slug']}")
    lines.extend(["### Field manual", ""])
    for guide in guides:
        lines.extend(
            [
                f"#### {guide['title']}",
                "",
                guide["body"],
                "",
                code_fence(guide["code"]),
                "",
            ]
        )

    lines.extend(["### Selected evidence", ""])
    for article in resolve_sources(manifest, book["sources"]):
        publication_id = f"{article['source']}:{article['source_id']}"
        publication = publications_by_id.get(publication_id) or publications_by_canonical.get(
            article["canonical_url"].rstrip("/")
        )
        if publication is None:
            raise ValueError(f"Resolved source is absent from deduplicated catalog: {publication_id}")
        lines.append(f"- {publication_link(publication)} ({source_label(publication)})")
    lines.append("")


def render_route_index(lines: list[str], publications: list[dict[str, Any]]) -> None:
    routes: dict[str, Counter[str]] = defaultdict(Counter)
    for publication in publications:
        for database in publication["databases"]:
            routes[database].update(publication["categories"])

    lines.extend(
        [
            "## Evidence routes",
            "",
            "Use these counts to locate the strongest parts of the corpus. One publication may cover multiple databases and topics; the exhaustive registry later in this file lists each publication exactly once.",
            "",
        ]
    )
    for database in sorted(routes, key=lambda value: (-sum(routes[value].values()), value)):
        topics = ", ".join(f"{name} ({count})" for name, count in routes[database].most_common())
        lines.extend([f"### {database}", "", topics, ""])


def render_registry(lines: list[str], publications: list[dict[str, Any]]) -> None:
    lines.extend(
        [
            "## Exhaustive source registry",
            "",
            "Every deduplicated publication in `archive-manifest.json` appears once below. Entries link to the canonical publication; the repository's `archive_path` is the durable local evidence when an external page changes or disappears.",
            "",
        ]
    )
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for publication in publications:
        grouped[publication["year"]].append(publication)

    rendered_ids: set[str] = set()
    for year in sorted(grouped, reverse=True):
        lines.extend([f"### {year}", ""])
        for publication in sorted(grouped[year], key=lambda item: (item["date"], item["title"]), reverse=True):
            if publication["id"] in rendered_ids:
                raise ValueError(f"Duplicate publication in registry: {publication['id']}")
            rendered_ids.add(publication["id"])
            summary = markdown_text(publication["summary"])
            lines.append(
                f"- {publication_link(publication)} - {source_label(publication)}; "
                f"archive: [{publication['archive_url']}]({publication['archive_url']})"
            )
            if summary:
                lines.append(f"  Evidence note: {summary}")
        lines.append("")

    expected_ids = {publication["id"] for publication in publications}
    if rendered_ids != expected_ids:
        missing = sorted(expected_ids - rendered_ids)
        raise ValueError(f"Registry coverage mismatch; missing {len(missing)} publications")


def build() -> str:
    catalog = build_catalog(ROOT)
    publications = catalog["publications"]
    publications_by_id = {publication["id"]: publication for publication in publications}
    publications_by_canonical = {
        publication["canonical_url"].rstrip("/"): publication for publication in publications
    }
    manifest_value = __import__("json").loads((ROOT / "archive-manifest.json").read_text(encoding="utf-8"))
    manifest = manifest_value["articles"]
    if len(publications_by_id) != len(publications):
        raise ValueError("Publication IDs are not unique")

    lines = [
        "---",
        "title: Source-Grounded Database Experience",
        'description: "Use when designing, diagnosing, migrating, or operating Oracle, PostgreSQL, YugabyteDB, MongoDB, distributed SQL, and related database systems."',
        "generated: true",
        "---",
        "",
        "# Source-Grounded Database Experience",
        "",
        f"This knowledge base distills {len(publications):,} unique publications ({manifest_value['article_count']:,} archived snapshots before cross-post deduplication) into {len(BOOKS)} practical playbooks. It preserves the complete source registry so an agent can move from an experienced heuristic back to the underlying publication and local snapshot.",
        "",
        "Generated by `python3.13 util/generate_db_skills.py`. Edit the curated minibook sources or generator, not this file.",
        "",
    ]
    render_experience_contract(lines)
    render_route_index(lines, publications)
    for book in BOOKS:
        render_book(lines, book, publications_by_id, publications_by_canonical, manifest)
    render_registry(lines, publications)
    lines.extend(
        [
            "## Coverage statement",
            "",
            f"- Unique publications represented: {len(publications):,}",
            f"- Archived snapshots inventoried: {manifest_value['article_count']:,}",
            f"- Practical playbooks: {len(BOOKS)}",
            f"- Field-manual procedures: {sum(len(TECHNICAL_GUIDES.get(book['slug'], [])) for book in BOOKS)}",
            f"- Publication years: {catalog['year_min']}-{catalog['year_max']}",
            "- Deduplication rule: when a non-LinkedIn record and LinkedIn record share a canonical URL, retain the LinkedIn publication in this knowledge base.",
            "- Classification rule: database, category, and version labels are regex-assisted discovery metadata, not claims that every paragraph applies to every listed product.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    content = build()
    OUTPUT.write_text(content, encoding="utf-8")
    registry_entries = len(re.findall(r"^- \[.*?\]\(https?://", content, flags=re.MULTILINE))
    print(f"Wrote {OUTPUT} ({len(content):,} characters; {registry_entries:,} linked evidence entries)")


if __name__ == "__main__":
    main()