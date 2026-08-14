#!/usr/bin/env python3
"""Analyze evaluative framing of databases across the publication archive."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from build_publication_map import (
    build_catalog,
    load_ai_descriptions,
    load_snapshot,
    normalize_text,
)


DATABASE_ALIASES = {
    "Oracle Database": r"\boracle(?: database)?\b|\bexadata\b",
    "PostgreSQL": r"\bpostgres(?:ql)?\b",
    "YugabyteDB": r"\byugabyte(?:db)?\b",
    "MongoDB": r"\bmongodb\b|\bmongo\b|\bwiredtiger\b",
    "Microsoft SQL Server": r"\b(?:microsoft )?sql server\b|\bt-sql\b",
    "MySQL": r"\bmysql\b|\bmariadb\b",
    "Amazon Aurora": r"\b(?:amazon |aws )?aurora\b",
    "Amazon DynamoDB": r"\bdynamodb\b",
    "DocumentDB": r"\bdocumentdb\b",
    "CockroachDB": r"\bcockroachdb\b",
    "Cassandra": r"\bcassandra\b",
    "SQLite": r"\bsqlite\b",
    "Db2": r"\bdb2\b",
    "SAP HANA": r"\bsap hana\b|\bhana database\b",
    "Azure HorizonDB": r"\b(?:azure )?horizondb\b",
}

POSITIVE_SIGNALS = {
    "advantage": 1,
    "benefit": 1,
    "better": 1,
    "efficient": 1,
    "elegant": 1,
    "excellent": 2,
    "fast": 1,
    "faster": 1,
    "flexible": 1,
    "good": 1,
    "great": 2,
    "improvement": 1,
    "improved": 1,
    "impressive": 2,
    "powerful": 1,
    "recommended": 1,
    "resilient": 1,
    "robust": 1,
    "scalable": 1,
    "useful": 1,
    "works well": 2,
}

CRITICAL_SIGNALS = {
    "bad": 1,
    "bug": 2,
    "complex": 1,
    "dangerous": 2,
    "drawback": 1,
    "expensive": 1,
    "inefficient": 2,
    "lack": 1,
    "limitation": 1,
    "problem": 1,
    "regression": 2,
    "slow": 1,
    "slower": 1,
    "unsupported": 1,
    "worse": 2,
    "wrong result": 3,
}

INTENT_SIGNALS = [
    ("bug diagnosis", r"\bbug\b|\bwrong results?\b|\bregression\b|\berror\b|\bfail(?:s|ed|ure)?\b"),
    ("workaround", r"\bworkaround\b|\bwork around\b|\bmitigat(?:e|ion)\b"),
    ("benchmark", r"\bbenchmark\b|\bpgbench\b|\bycsb\b|\blatency\b|\bthroughput\b|\biops\b"),
    ("comparison", r"\bversus\b|\bvs\.?\b|\bcompar(?:e|ed|ing|ison)\b|\bunlike\b"),
    ("new feature", r"\bnew feature\b|\bwhat(?:'s| is) new\b|\bintroduc(?:e|ed|ing)\b|\bpreview\b|\bannounc(?:e|ed|ement)\b"),
    ("limitation", r"\blimitation\b|\bnot supported\b|\bcannot\b|\bmissing\b|\boverhead\b|\btoo (?:slow|expensive)\b"),
    ("operational guidance", r"\bmonitor(?:ing)?\b|\bconfigur(?:e|ation)\b|\binstall(?:ing|ation)?\b|\btroubleshoot(?:ing)?\b|\bdiagnos(?:e|is|ing)\b"),
    ("technical exploration", r"\bexplain\b|\binternals?\b|\bunderstand(?:ing)?\b|\bhow .* works?\b|\btest(?:ed|ing)?\b|\bexperiment\b"),
]

EVIDENCE_PATTERN = re.compile(
    r"\b(?:benchmark|demo(?:nstrate)?|evidence|experiment|explain(?: analyze)?|measure(?:d|ment)?|"
    r"observ(?:e|ed|ation)|plan|profil(?:e|ing)|reproduc(?:e|ed|ible)|test(?:ed|ing)?|trace)\b",
    re.IGNORECASE,
)
PRODUCT_WIDE_PATTERN = re.compile(
    r"\b(?:always|never|inherently|fundamentally|overall|the best|the worst|all databases?|no database)\b",
    re.IGNORECASE,
)
ARCHITECTURE_PATTERN = re.compile(
    r"\b(?:architecture|distributed|consensus|document model|relational|storage engine|mvcc|replication|sharding)\b",
    re.IGNORECASE,
)
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")
RELATION_CUE_PATTERN = re.compile(
    r"\b(?:advantage|benefit|strength|disadvantage|drawback|limitation|better|worse|"
    r"combine|bring|deliver|offer|provide|retain|inherit|overcome|solve|address|avoid|lack|"
    r"substitute|replace|match|parity|compatible|catch up)\w*\b",
    re.IGNORECASE,
)
EVALUATIVE_CUE_PATTERN = re.compile(
    rf"\b(?:{'|'.join(map(re.escape, POSITIVE_SIGNALS))}|{'|'.join(map(re.escape, CRITICAL_SIGNALS))}|"
    r"downtime|data loss|single point(?:s)? of failure)\b",
    re.IGNORECASE,
)
POSITIVE_RELATION_NOUN = r"advantage(?:s)?|benefit(?:s)?|strength(?:s)?"
CRITICAL_RELATION_NOUN = r"disadvantage(?:s)?|drawback(?:s)?|limitation(?:s)?|weakness(?:es)?"


def signal_hits(
    text: str, signals: dict[str, int], target_alias: str | None = None
) -> list[dict[str, Any]]:
    hits = []
    folded = text.casefold()
    target_positions = []
    other_positions = []
    if target_alias:
        target_positions = [
            (match.start() + match.end()) / 2
            for match in re.finditer(target_alias, text, re.IGNORECASE)
        ]
        for alias in DATABASE_ALIASES.values():
            if alias == target_alias:
                continue
            other_positions.extend(
                (match.start() + match.end()) / 2
                for match in re.finditer(alias, text, re.IGNORECASE)
            )
    for phrase, weight in signals.items():
        for match in re.finditer(rf"\b{re.escape(phrase)}\b", folded):
            signal_position = (match.start() + match.end()) / 2
            if target_positions:
                target_distance = min(abs(signal_position - position) for position in target_positions)
                other_distance = min(
                    (abs(signal_position - position) for position in other_positions),
                    default=math.inf,
                )
                if other_distance < target_distance:
                    continue
            prefix = folded[max(0, match.start() - 18):match.start()]
            surroundings = folded[max(0, match.start() - 30):match.end() + 30]
            if re.search(r"\b(?:not|no|isn't|wasn't|without)\s+$", prefix):
                continue
            if signals is POSITIVE_SIGNALS and re.search(
                rf"\b(?:claim|market|say|state|tout)\w*\b.{{0,36}}\b{re.escape(phrase)}\b",
                surroundings,
            ):
                continue
            if signals is CRITICAL_SIGNALS and re.search(
                rf"\b(?:avoid(?:s|ed|ing)?|lower(?:s|ed|ing)?|minimi[sz](?:e|es|ed|ing)|reduc(?:e|es|ed|ing))\b"
                rf".{{0,24}}\b{re.escape(phrase)}\b",
                surroundings,
            ):
                continue
            if signals is CRITICAL_SIGNALS and re.search(
                rf"\b(?:myth|supposed(?:ly)?|minimal risks? of)\b.*\b{re.escape(phrase)}\b|"
                rf"\b{re.escape(phrase)}\b.*\b(?:myth|is fixed|was fixed|has been fixed)\b",
                surroundings,
            ):
                continue
            if signals is CRITICAL_SIGNALS and phrase == "problem" and re.search(
                r"\b(?:introduce|define|describe|show)\s+the\s+problem\b.*\b(?:show|demonstrat|explain|using)\w*\b",
                folded[max(0, match.start() - 120):match.end() + 120],
            ):
                continue
            hits.append({"phrase": phrase, "weight": weight})
    if signals is POSITIVE_SIGNALS:
        improvement_pattern = re.compile(
            r"\b(?:avoid(?:s|ed|ing)?|lower(?:s|ed|ing)?|minimi[sz](?:e|es|ed|ing)|reduc(?:e|es|ed|ing))\b"
            r".{0,32}\b(?:cost|data loss|downtime|failure|latency|overhead|risk)\b"
        )
        for match in improvement_pattern.finditer(folded):
            signal_position = (match.start() + match.end()) / 2
            if target_positions:
                target_distance = min(abs(signal_position - position) for position in target_positions)
                other_distance = min(
                    (abs(signal_position - position) for position in other_positions),
                    default=math.inf,
                )
                if other_distance < target_distance:
                    continue
            hits.append({"phrase": "reduced cost, risk, or downtime", "weight": 1})
    return hits


def mention_contexts(text: str, alias_pattern: str) -> list[str]:
    sentences = [normalize_text(sentence) for sentence in SENTENCE_PATTERN.split(text)]
    sentences = [sentence for sentence in sentences if sentence]
    contexts = []
    for sentence in sentences:
        if re.search(alias_pattern, sentence, re.IGNORECASE):
            contexts.append(sentence)
    return list(dict.fromkeys(contexts))


def database_mentions(text: str) -> list[tuple[str, int, int]]:
    mentions = []
    for database, alias in DATABASE_ALIASES.items():
        mentions.extend((database, match.start(), match.end()) for match in re.finditer(alias, text, re.IGNORECASE))
    return sorted(mentions, key=lambda item: item[1])


def evaluative_sentences(text: str) -> list[str]:
    sentences = [normalize_text(sentence) for sentence in SENTENCE_PATTERN.split(text)]
    result = []
    for sentence in sentences:
        named_databases = {database for database, _, _ in database_mentions(sentence)}
        if named_databases and (RELATION_CUE_PATTERN.search(sentence) or EVALUATIVE_CUE_PATTERN.search(sentence)) and len(sentence) <= 700:
            result.append(sentence)
    return list(dict.fromkeys(result))[:12]


def relation_hits(text: str, target_database: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    positive = []
    critical = []
    for sentence in [normalize_text(value) for value in SENTENCE_PATTERN.split(text) if normalize_text(value)]:
        mentions = database_mentions(sentence)
        target_mentions = [mention for mention in mentions if mention[0] == target_database]
        if not target_mentions:
            continue

        def add(target: list[dict[str, Any]], phrase: str) -> None:
            if phrase not in {hit["phrase"] for hit in target}:
                target.append({"phrase": phrase, "weight": 1})

        folded = sentence.casefold()
        for _, start, end in target_mentions:
            before = folded[max(0, start - 90):start]
            after = folded[end:min(len(folded), end + 120)]
            possessive_after = folded[end:min(len(folded), end + 70)]

            if re.search(rf"\b(?:{POSITIVE_RELATION_NOUN})\b(?:\s+\w+){{0,4}}\s+of\s+(?:\w+\s+){{0,4}}$", before):
                add(positive, "named source of advantages")
            if re.search(rf"\b(?:{CRITICAL_RELATION_NOUN})\b(?:\s+\w+){{0,4}}\s+of\s+(?:\w+\s+){{0,4}}$", before):
                add(critical, "named source of disadvantages")
            if re.match(rf"(?:'s|’s)?(?:\s+\w+){{0,4}}\s+\b(?:{POSITIVE_RELATION_NOUN})\b", possessive_after):
                add(positive, "possesses stated advantages")
            if re.match(rf"(?:'s|’s)?(?:\s+\w+){{0,4}}\s+\b(?:{CRITICAL_RELATION_NOUN})\b", possessive_after):
                add(critical, "possesses stated disadvantages")

            better_after = re.search(r"\bbetter\s+than\b", after)
            better_before = re.search(r"\bbetter\s+than(?:\s+\w+){0,5}\s*$", before)
            worse_after = re.search(r"\bworse\s+than\b", after)
            worse_before = re.search(r"\bworse\s+than(?:\s+\w+){0,5}\s*$", before)
            reported_comparison = bool(re.search(r"\b(?:claim|market|say|state|tout)\w*\b", before[-45:] + after[:45]))
            if better_after and not reported_comparison:
                add(positive, "better side of comparison")
            if better_before and not reported_comparison:
                add(critical, "worse side of comparison")
            if worse_after and not reported_comparison:
                add(critical, "worse side of comparison")
            if worse_before and not reported_comparison:
                add(positive, "better side of comparison")

            if re.search(r"\b(?:combine|bring|deliver|offer|provide|retain|inherit)\w*\b", after[:45]) and re.search(
                rf"\b(?:{POSITIVE_RELATION_NOUN})\b", after
            ):
                add(positive, "delivers stated advantages")
            if re.search(r"\b(?:overcome|solve|address|avoid)\w*\b", after[:55]) and re.search(
                rf"\b(?:{CRITICAL_RELATION_NOUN}|problem|risk|downtime|data loss)\b", after
            ):
                add(positive, "overcomes stated disadvantages")
            if re.search(r"\b(?:require|involve|cause|risk)\w*\b", after[:45]) and re.search(
                r"\b(?:downtime|data loss|single point(?:s)? of failure)\b", after
            ):
                add(critical, "incurs stated availability disadvantage")
            if re.search(r"\b(?:claim|market|tout)\w*\b", after[:35]) and re.search(
                r"\b(?:but|however|yet)\b.{0,90}\b(?:lack|mislead|unsupported|unrealistic|wrong)\w*\b",
                after,
            ):
                add(critical, "reported claim is challenged")
            if re.search(
                r"\b(?:cannot|can't|could not|couldn't|fail(?:s|ed)? to|tries? to|attempts? to)\s+"
                r"(?:fully\s+)?(?:substitute|replace|match|equal|reach)\w*(?:\s+\w+){0,5}\s*$",
                before,
            ):
                add(positive, "capability benchmark")
            if re.search(
                r"\b(?:catch(?:es|ing)? up to|reach(?:es|ed|ing)? parity with|"
                r"become(?:s|ing)? as good as|now match(?:es|ed|ing)?)\s*$",
                before,
            ):
                add(positive, "parity benchmark")
            if re.search(
                r"\b(?:catch(?:es|ing)? up to|reach(?:es|ed|ing)? parity with|now match(?:es|ed|ing)?)\b",
                after[:55],
            ):
                add(positive, "reaches benchmark parity")
            if re.search(
                r"\bmatch(?:es|ed|ing)?\s+(?:the\s+)?(?:features|capabilities|behavior|semantics)\s+of\s*$",
                before,
            ):
                add(positive, "feature parity benchmark")
            if re.search(
                r"\bmatch(?:es|ed|ing)?\s+(?:the\s+)?(?:features|capabilities|behavior|semantics)\s+of\b",
                after[:90],
            ):
                add(positive, "achieves feature parity")
    return positive, critical


def preferred_publication_url(publication: dict[str, Any]) -> str:
    return publication.get("canonical_url") or publication["read_url"]


def classify_mention(
    publication: dict[str, Any], database: str, curated_summary: str
) -> dict[str, Any] | None:
    alias_pattern = DATABASE_ALIASES.get(database)
    if not alias_pattern:
        return None
    title_summary = normalize_text(f"{publication['title']}. {curated_summary}")
    contexts = mention_contexts(title_summary, alias_pattern)
    explicit_mentions = len(re.findall(alias_pattern, title_summary, re.IGNORECASE))
    if not explicit_mentions:
        return None

    analysis_text = normalize_text(" ".join(contexts))
    positive_hits = signal_hits(analysis_text, POSITIVE_SIGNALS, alias_pattern)
    critical_hits = signal_hits(analysis_text, CRITICAL_SIGNALS, alias_pattern)
    relation_positive, relation_critical = relation_hits(analysis_text, database)
    positive_hits.extend(relation_positive)
    critical_hits.extend(relation_critical)
    positive_weight = sum(hit["weight"] for hit in positive_hits)
    critical_weight = sum(hit["weight"] for hit in critical_hits)
    raw_score = positive_weight - critical_weight
    scale = max(1.0, math.sqrt(max(1, len(contexts))))
    normalized_score = raw_score / scale
    if normalized_score >= 2:
        evaluation = 2
    elif normalized_score > 0:
        evaluation = 1
    elif normalized_score <= -2:
        evaluation = -2
    elif normalized_score < 0:
        evaluation = -1
    else:
        evaluation = 0

    intent = "technical explanation"
    for candidate, pattern in INTENT_SIGNALS:
        if re.search(pattern, analysis_text, re.IGNORECASE):
            intent = candidate
            break

    if PRODUCT_WIDE_PATTERN.search(analysis_text):
        scope = "product-wide"
    elif ARCHITECTURE_PATTERN.search(analysis_text):
        scope = "architectural trade-off"
    else:
        scope = "specific feature or behavior"

    ranked_contexts = []
    for context in contexts:
        positive = sum(hit["weight"] for hit in signal_hits(context, POSITIVE_SIGNALS, alias_pattern))
        critical = sum(hit["weight"] for hit in signal_hits(context, CRITICAL_SIGNALS, alias_pattern))
        ranked_contexts.append((abs(positive - critical), positive + critical, context))
    evidence_excerpt = max(ranked_contexts, key=lambda item: (item[0], item[1]))[2][:420]
    signal_count = len(positive_hits) + len(critical_hits)
    confidence = "high" if curated_summary and signal_count >= 2 else "medium" if curated_summary else "low"

    return {
        "publication_id": publication["id"],
        "database": database,
        "date": publication["date"],
        "employment_period": publication["employment_period"],
        "title": publication["title"],
        "url": preferred_publication_url(publication),
        "source": publication["source_key"],
        "evaluation": evaluation,
        "positive_weight": positive_weight,
        "critical_weight": critical_weight,
        "mixed": positive_weight > 0 and critical_weight > 0,
        "intent": intent,
        "scope": scope,
        "evidence_backed": bool(EVIDENCE_PATTERN.search(analysis_text)),
        "confidence": confidence,
        "summary_source": "curated" if curated_summary else "title only",
        "explicit_mentions": explicit_mentions,
        "positive_signals": sorted({hit["phrase"] for hit in positive_hits}),
        "critical_signals": sorted({hit["phrase"] for hit in critical_hits}),
        "evidence_excerpt": evidence_excerpt,
        "relation_aware": bool(relation_positive or relation_critical),
    }


def build_analysis(root: Path) -> dict[str, Any]:
    catalog = build_catalog(root)
    curated_summaries = load_ai_descriptions(root)
    manifest = json.loads((root / "archive-manifest.json").read_text(encoding="utf-8"))
    articles = {f"{article['source']}:{article['source_id']}": article for article in manifest["articles"]}
    records = []
    for publication in catalog["publications"]:
        curated_summary = curated_summaries.get(publication["id"], "")
        body, _ = load_snapshot(root, articles[publication["id"]])
        evaluative_prose = evaluative_sentences(body)
        analysis_summary = normalize_text(" ".join([curated_summary, *evaluative_prose]))
        prose_databases = {
            database for sentence in evaluative_prose for database, _, _ in database_mentions(sentence)
        }
        for database in sorted(set(publication["databases"]) | prose_databases):
            record = classify_mention(publication, database, analysis_summary)
            if record:
                records.append(record)

    period_lookup = {period["key"]: period for period in catalog["employment_periods"]}
    database_counts = Counter(record["database"] for record in records)
    aggregates = {}
    for database in database_counts:
        database_records = [record for record in records if record["database"] == database]
        periods = {}
        for period_key in period_lookup:
            period_records = [
                record for record in database_records if record["employment_period"] == period_key
            ]
            if not period_records:
                continue
            evaluations = [record["evaluation"] for record in period_records]
            critical = [record for record in period_records if record["evaluation"] < 0]
            periods[period_key] = {
                "count": len(period_records),
                "mean_evaluation": round(sum(evaluations) / len(evaluations), 3),
                "distribution": {
                    str(score): evaluations.count(score) for score in range(-2, 3)
                },
                "supportive_share": round(sum(score > 0 for score in evaluations) / len(evaluations), 4),
                "critical_share": round(sum(score < 0 for score in evaluations) / len(evaluations), 4),
                "mixed_share": round(sum(record["mixed"] for record in period_records) / len(period_records), 4),
                "evidence_backed_critical_share": round(
                    sum(record["evidence_backed"] for record in critical) / len(critical), 4
                ) if critical else None,
                "product_wide_critical_count": sum(
                    record["scope"] == "product-wide" for record in critical
                ),
            }
        aggregates[database] = {"count": len(database_records), "periods": periods}
    return {
        "schema_version": 1,
        "method": "conservative-relation-aware-sentiment-v3",
        "publication_count": catalog["publication_count"],
        "mention_count": len(records),
        "database_counts": dict(database_counts.most_common()),
        "employment_periods": [period_lookup[key] for key in period_lookup],
        "aggregates": aggregates,
        "records": sorted(records, key=lambda record: (record["date"], record["publication_id"], record["database"])),
    }


def write_analysis(path: Path, analysis: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    formatted = json.dumps(analysis, ensure_ascii=False, indent=2)
    path.write_text(formatted + "\n", encoding="utf-8")
    browser_payload = json.dumps(analysis, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    path.with_suffix(".js").write_text(
        f"window.DATABASE_TONE_DATA={browser_payload};\n", encoding="utf-8"
    )


def blend_color(start: tuple[int, int, int], end: tuple[int, int, int], amount: float) -> str:
    channels = [round(value + (end[index] - value) * amount) for index, value in enumerate(start)]
    return f"#{''.join(f'{channel:02x}' for channel in channels)}"


def matrix_color(score: float, count: int, maximum_count: int) -> str:
    volume = 0.04 + 0.96 * math.sqrt(max(0, count - 1) / max(1, maximum_count - 1))
    gray = (222, 220, 212)
    tone = (226, 74, 74) if score < 0 else (53, 201, 111) if score > 0 else (33, 135, 199)
    score_emphasis = 1 if score == 0 else min(1, 0.45 + abs(score) / 2)
    return blend_color(gray, tone, min(1, volume * score_emphasis))


def write_social_card(path: Path, analysis: dict[str, Any]) -> None:
    databases = list(analysis["database_counts"])[:8]
    periods = list(reversed(analysis["employment_periods"]))
    maximum_count = max(
        values["count"]
        for aggregate in analysis["aggregates"].values()
        for values in aggregate["periods"].values()
    )
    left = 290
    top = 258
    cell_width = 122
    cell_height = 35
    period_labels = []
    for index, period in enumerate(periods):
        x = left + index * cell_width + cell_width / 2
        period_labels.append(
            f'<text x="{x:.0f}" y="242" text-anchor="middle" class="period">{html.escape(period["company"])}</text>'
        )
    rows = []
    for row_index, database in enumerate(databases):
        y = top + row_index * (cell_height + 4)
        rows.append(f'<text x="66" y="{y + 24}" class="database">{html.escape(database)}</text>')
        for column_index, period in enumerate(periods):
            x = left + column_index * cell_width
            values = analysis["aggregates"][database]["periods"].get(period["key"])
            if not values:
                rows.append(f'<rect x="{x}" y="{y}" width="{cell_width - 5}" height="{cell_height}" class="empty"/>')
                continue
            color = matrix_color(values["mean_evaluation"], values["count"], maximum_count)
            score = values["mean_evaluation"]
            score_text = f"{score:+.2f}" if score else "0.00"
            rows.append(
                f'<rect x="{x}" y="{y}" width="{cell_width - 5}" height="{cell_height}" fill="{color}"/>'
                f'<text x="{x + 8}" y="{y + 16}" class="score">{score_text}</text>'
                f'<text x="{x + 8}" y="{y + 30}" class="mentions">{values["count"]} mentions</text>'
            )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs><pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M34 0H0V34" fill="none" stroke="#182321" stroke-opacity=".035"/></pattern></defs>
  <style>
    text {{ fill: #182321; font-family: Arial, Helvetica, sans-serif; }}
    .eyebrow {{ fill: #236b66; font-size: 15px; font-weight: 700; letter-spacing: 2px; }}
    .title {{ font-family: Georgia, serif; font-size: 48px; font-weight: 700; }}
    .subtitle {{ fill: #65716e; font-size: 17px; }}
    .period {{ fill: #65716e; font-size: 12px; font-weight: 700; }}
    .database {{ font-family: Georgia, serif; font-size: 19px; font-weight: 700; }}
    .score {{ font-size: 14px; font-weight: 700; }}
    .mentions {{ fill: #344440; font-size: 10px; }}
    .legend {{ fill: #65716e; font-size: 12px; }}
    .empty {{ fill: #eceae3; stroke: #d7d4c9; }}
  </style>
  <rect width="1200" height="630" fill="#f4f2ea"/><rect width="1200" height="630" fill="url(#grid)"/>
  <rect x="0" width="18" height="630" fill="#236b66"/>
  <text x="66" y="58" class="eyebrow">AI CORPUS ANALYSIS · FRANCK PACHOT</text>
  <text x="66" y="116" class="title">Did my employer change how I write</text>
  <text x="66" y="168" class="title">about databases?</text>
    <text x="66" y="205" class="subtitle">Average framing by employer period · top eight databases by mentions</text>
  {''.join(period_labels)}{''.join(rows)}
  <circle cx="70" cy="590" r="7" fill="#e24a4a"/><text x="84" y="594" class="legend">critical</text>
  <circle cx="165" cy="590" r="7" fill="#2187c7"/><text x="179" y="594" class="legend">neutral</text>
  <circle cx="255" cy="590" r="7" fill="#35c96f"/><text x="269" y="594" class="legend">supportive</text>
  <text x="1134" y="594" text-anchor="end" class="legend">stronger color = more mentions</text>
</svg>'''
    svg_path = path / "social-card.svg"
    png_path = path / "social-card.png"
    svg_path.write_text(svg, encoding="utf-8")
    browser_candidates = [
        shutil.which("msedge"),
        shutil.which("google-chrome"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    browser = next((candidate for candidate in browser_candidates if candidate and Path(candidate).exists()), None)
    if browser:
        subprocess.run(
            [str(browser), "--headless", "--disable-gpu", "--hide-scrollbars", "--window-size=1200,630", f"--screenshot={png_path}", svg_path.as_uri()],
            check=True,
            capture_output=True,
        )
    elif not png_path.exists():
        raise RuntimeError("Chrome or Edge is required to create the analysis social card")


def validate_analysis(analysis: dict[str, Any]) -> None:
    period_keys = {period["key"] for period in analysis["employment_periods"]}
    if sum(analysis["database_counts"].values()) != analysis["mention_count"]:
        raise ValueError("Database counts do not sum to the mention count")
    for record in analysis["records"]:
        if record["database"] not in analysis["database_counts"]:
            raise ValueError(f"Unknown database in record: {record['database']}")
        if record["employment_period"] not in period_keys:
            raise ValueError(f"Unknown employment period: {record['employment_period']}")
        if record["evaluation"] not in range(-2, 3):
            raise ValueError(f"Invalid evaluation: {record['evaluation']}")
    for database, aggregate in analysis["aggregates"].items():
        period_total = sum(period["count"] for period in aggregate["periods"].values())
        if period_total != aggregate["count"] or period_total != analysis["database_counts"][database]:
            raise ValueError(f"Aggregate count mismatch for {database}")


def print_audit(analysis: dict[str, Any], limit: int = 4) -> None:
    for database, count in analysis["database_counts"].items():
        if count < 10:
            continue
        records = [record for record in analysis["records"] if record["database"] == database]
        print(f"\n## {database} ({count})")
        rankings = [
            ("most supportive", sorted(records, key=lambda record: (-record["evaluation"], -record["positive_weight"], record["critical_weight"]))),
            ("most critical", sorted(records, key=lambda record: (record["evaluation"], -record["critical_weight"], record["positive_weight"]))),
        ]
        for label, ranked in rankings:
            print(f"  {label}:")
            for record in ranked[:limit]:
                print(
                    f"    [{record['evaluation']:+d}] {record['date']} {record['title']} | "
                    f"{record['evidence_excerpt']}"
                )


def print_summary(analysis: dict[str, Any]) -> None:
    period_labels = {
        period["key"]: f"{period['company']} {period['range']}"
        for period in analysis["employment_periods"]
    }
    for database, aggregate in analysis["aggregates"].items():
        print(f"\n## {database} ({aggregate['count']})")
        for period_key, values in aggregate["periods"].items():
            print(
                f"  {period_labels[period_key]}: n={values['count']}, "
                f"mean={values['mean_evaluation']:+.3f}, "
                f"supportive={values['supportive_share']:.1%}, "
                f"critical={values['critical_share']:.1%}, "
                f"product-wide-critical={values['product_wide_critical_count']}"
            )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit", action="store_true", help="Print ranked evidence for classifier review")
    parser.add_argument("--summary", action="store_true", help="Print employer-period aggregates")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "analysis" / "database-tone" / "data.json"
    analysis = build_analysis(root)
    validate_analysis(analysis)
    write_analysis(output, analysis)
    write_social_card(output.parent, analysis)
    print(f"Wrote {output} with {analysis['mention_count']} substantive database mentions")
    print(json.dumps(analysis["database_counts"], indent=2))
    if args.audit:
        print_audit(analysis)
    if args.summary:
        print_summary(analysis)


if __name__ == "__main__":
    main()
