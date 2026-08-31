#!/usr/bin/env python3
"""Build the publication impact dashboard from dated metric snapshots."""

from __future__ import annotations

import argparse
import datetime
import html
import json
from pathlib import Path
from typing import Any


SOURCE_LABELS = {
    "dev.to": "DEV Community",
    "linkedin": "LinkedIn",
    "microsoft-techcommunity": "Microsoft Tech Community",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def archived_source_counts(root: Path) -> dict[str, int]:
  manifest_path = root / "archive-manifest.json"
  if not manifest_path.exists():
    return {}
  sources = read_json(manifest_path).get("sources", {})
  return {source: count for source, count in sources.items() if isinstance(count, int)}


def latest_observations(root: Path) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "impact").glob("*/*.json")):
        snapshot = read_json(path)
        for publication in snapshot.get("publications", []):
            publication_id = publication.get("publication_id")
            collected_at = publication.get("collected_at", snapshot.get("collected_at", ""))
            if not isinstance(publication_id, str) or not isinstance(collected_at, str):
                continue
            candidate = {**publication, "collected_at": collected_at}
            current = latest.get(publication_id)
            if current is None or collected_at > current.get("collected_at", ""):
                latest[publication_id] = candidate
    return sorted(
        latest.values(),
        key=lambda publication: (
            publication.get("published_at", ""),
            publication.get("title", ""),
        ),
        reverse=True,
    )


def metric(publication: dict[str, Any], name: str) -> int | None:
    value = publication.get("metrics", {}).get(name)
    return value if isinstance(value, int) else None


def article_views(publication: dict[str, Any]) -> int | None:
    if publication.get("source") == "dev.to":
        return metric(publication, "page_views")
    if publication.get("source") == "linkedin":
        return metric(publication, "article_views")
    return metric(publication, "article_views") or metric(publication, "page_views")


def format_number(value: int | None) -> str:
    return f"{value:,}" if value is not None else "Not available"


def source_summary(
  publications: list[dict[str, Any]], source: str, archived_count: int = 0
) -> dict[str, Any]:
    selected = [publication for publication in publications if publication.get("source") == source]
    views = [value for publication in selected if (value := article_views(publication)) is not None]
    impressions = [
        value
        for publication in selected
        if (value := metric(publication, "feed_post_impressions")) is not None
    ]
    return {
        "source": source,
        "label": SOURCE_LABELS.get(source, source),
        "publications": len(selected),
        "archived_publications": archived_count,
        "article_views": sum(views),
        "impressions": sum(impressions),
    }


def publication_row(publication: dict[str, Any]) -> str:
    source = publication.get("source", "")
    source_label = SOURCE_LABELS.get(source, source)
    views = article_views(publication)
    impressions = metric(publication, "feed_post_impressions")
    reactions = metric(publication, "reactions")
    comments = metric(publication, "comments")
    canonical_url = html.escape(publication.get("canonical_url", ""), quote=True)
    title = html.escape(publication.get("title", ""))
    published_at = html.escape(publication.get("published_at", ""))
    collected_at = html.escape(publication.get("collected_at", ""))
    searchable = html.escape(f"{publication.get('title', '')} {source_label}".lower(), quote=True)
    return f'''      <tr data-source="{html.escape(source, quote=True)}" data-search="{searchable}" data-views="{views if views is not None else -1}" data-date="{published_at}">
        <td><time datetime="{published_at}">{published_at[:10]}</time></td>
        <td><a href="{canonical_url}" target="_blank" rel="noopener">{title}</a><small>Measured {collected_at[:10]}</small></td>
        <td><span class="impact-source impact-source--{html.escape(source, quote=True)}">{html.escape(source_label)}</span></td>
        <td class="impact-number">{format_number(views)}</td>
        <td class="impact-number">{format_number(impressions)}</td>
        <td class="impact-number">{format_number(reactions)}</td>
        <td class="impact-number">{format_number(comments)}</td>
      </tr>'''


def build_document(
    publications: list[dict[str, Any]], source_counts: dict[str, int] | None = None
) -> str:
    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    source_counts = source_counts or {}
    sources = sorted({publication.get("source", "") for publication in publications})
    summaries = [
        source_summary(publications, source, source_counts.get(source, 0))
        for source in sources
    ]
    linkedin = next((summary for summary in summaries if summary["source"] == "linkedin"), None)
    total_views = sum(summary["article_views"] for summary in summaries)
    eligible_archive_count = sum(
        source_counts.get(source, 0) for source in ("dev.to", "linkedin")
    )
    latest_collection = max(
        (publication.get("collected_at", "") for publication in publications), default=""
    )
    summary_markup = "\n".join(
        f'''        <div class="impact-summary__row">
          <span>{html.escape(summary["label"])}</span>
          <strong>{summary["publications"]:,} / {summary["archived_publications"]:,}</strong>
          <span>{summary["article_views"]:,} article views</span>
          <span>{summary["impressions"]:,} impressions</span>
        </div>'''
        for summary in summaries
    )
    source_options = "\n".join(
        f'            <option value="{html.escape(source, quote=True)}">{html.escape(SOURCE_LABELS.get(source, source))}</option>'
        for source in sources
    )
    rows = "\n".join(publication_row(publication) for publication in publications)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Measured article views, impressions, and engagement for Franck Pachot's database publications.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://franckpachot.github.io/pages/impact.html">
  <title>Publication Impact | Franck Pachot</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;family=Newsreader:opsz,wght@6..72,600&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="home/style.css">
  <style>
    .impact-main {{ padding-top: 42px; }}
    .impact-intro {{ display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(300px, .8fr); gap: 56px; align-items: end; padding-bottom: 42px; border-bottom: 1px solid var(--ink); }}
    .impact-intro h1 {{ max-width: 760px; }}
    .impact-method {{ color: var(--muted); font-size: 14px; line-height: 1.55; margin: 0; }}
    .impact-totals {{ display: grid; grid-template-columns: repeat(3, 1fr); border-bottom: 1px solid var(--line); }}
    .impact-total {{ padding: 28px 24px 30px 0; }}
    .impact-total + .impact-total {{ border-left: 1px solid var(--line); padding-left: 24px; }}
    .impact-total span {{ color: var(--muted); display: block; font: 11px "IBM Plex Mono", monospace; text-transform: uppercase; }}
    .impact-total strong {{ display: block; font: 600 38px "Newsreader", serif; margin-top: 6px; }}
    .impact-total small {{ color: var(--muted); }}
    .impact-breakdown {{ padding: 36px 0; border-bottom: 1px solid var(--line); }}
    .impact-summary {{ border-top: 1px solid var(--ink); }}
    .impact-summary__row {{ display: grid; grid-template-columns: minmax(180px, 1fr) 90px 170px 160px; gap: 16px; padding: 13px 0; border-bottom: 1px solid var(--line); align-items: baseline; }}
    .impact-summary__row span:not(:first-child) {{ color: var(--muted); font-size: 13px; }}
    .impact-explorer {{ padding: 40px 0; }}
    .impact-controls {{ display: grid; grid-template-columns: minmax(260px, 1fr) 220px 190px; gap: 10px; padding: 16px; background: var(--ink); border-radius: var(--radius); margin: 20px 0 0; }}
    .impact-controls label {{ color: #b9c3c9; display: grid; font: 10px "IBM Plex Mono", monospace; gap: 6px; text-transform: uppercase; }}
    .impact-controls input, .impact-controls select {{ background: #22313b; border: 1px solid #42505b; border-radius: 4px; color: white; height: 40px; padding: 0 10px; width: 100%; }}
    .impact-table-wrap {{ overflow-x: auto; }}
    .impact-table {{ display: table; min-width: 940px; width: 100%; }}
    .impact-table th {{ color: var(--muted); font: 10px "IBM Plex Mono", monospace; text-transform: uppercase; }}
    .impact-table td {{ font-size: 14px; vertical-align: top; }}
    .impact-table td:nth-child(2) {{ min-width: 320px; }}
    .impact-table td a {{ font: 600 18px "Newsreader", serif; text-underline-offset: 3px; }}
    .impact-table td small {{ color: var(--muted); display: block; margin-top: 4px; }}
    .impact-number {{ font-family: "IBM Plex Mono", monospace; text-align: right; white-space: nowrap; }}
    .impact-source {{ border: 1px solid var(--line); border-radius: 3px; display: inline-block; font-size: 11px; padding: 3px 7px; white-space: nowrap; }}
    .impact-empty {{ color: var(--muted); padding: 38px 0; text-align: center; }}
    @media (max-width: 800px) {{
      .impact-intro {{ grid-template-columns: 1fr; gap: 24px; }}
      .impact-totals {{ grid-template-columns: 1fr; }}
      .impact-total + .impact-total {{ border-left: 0; border-top: 1px solid var(--line); padding-left: 0; }}
      .impact-summary__row {{ grid-template-columns: 1fr 70px; }}
      .impact-summary__row span:not(:first-child) {{ grid-column: 1 / -1; }}
      .impact-controls {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header class="masthead">
    <div class="masthead__inner">
      <a class="identity" href="./" aria-label="Franck Pachot database articles">
        <img class="identity__portrait" src="franck-pachot-linkedin.jpg" alt="" width="52" height="52">
        <span><strong>Franck Pachot</strong><small>Database Developer Advocate</small></span>
      </a>
      <p class="masthead__bio">Measured reach and engagement from publication platforms. <a href="./">Browse the article archive</a></p>
      <div class="masthead__range">Updated {html.escape(latest_collection[:10] or generated_at[:10])}</div>
    </div>
  </header>
  <main class="impact-main">
    <section class="impact-intro" aria-labelledby="impact-title">
      <div>
        <p class="eyebrow">Publication evidence</p>
        <h1 id="impact-title">Article impact, measured at the source</h1>
        <p class="lede">Views and engagement reported by the publishing platforms, kept as dated observations rather than blended estimates.</p>
      </div>
      <p class="impact-method"><strong>How to read this page.</strong> Article views measure opened articles. LinkedIn impressions measure feed exposure and are reported separately. Counters from different platforms are not directly comparable, and unavailable metrics are never inferred.</p>
    </section>
    <section class="impact-totals" aria-label="Impact totals">
      <div class="impact-total"><span>Measured publications</span><strong>{len(publications):,} / {eligible_archive_count:,}</strong><small>DEV and LinkedIn archive coverage</small></div>
      <div class="impact-total"><span>Article views</span><strong>{total_views:,}</strong><small>DEV and LinkedIn combined</small></div>
      <div class="impact-total"><span>LinkedIn impressions</span><strong>{linkedin["impressions"] if linkedin else 0:,}</strong><small>feed discovery, not article opens</small></div>
    </section>
    <section class="impact-breakdown" aria-labelledby="coverage-title">
      <div class="section-heading"><div><p class="eyebrow">Coverage</p><h2 id="coverage-title">Metrics by platform</h2></div></div>
      <div class="impact-summary">
{summary_markup}
      </div>
    </section>
    <section class="impact-explorer" aria-labelledby="articles-title">
      <div class="section-heading"><div><p class="eyebrow">Measured history</p><h2 id="articles-title"><span id="impact-count">{len(publications):,}</span> articles</h2></div></div>
      <form class="impact-controls" id="impact-controls" role="search">
        <label>Search<input id="impact-search" type="search" placeholder="Article title"></label>
        <label>Platform<select id="impact-source"><option value="">All measured platforms</option>
{source_options}
        </select></label>
        <label>Sort<select id="impact-sort"><option value="views">Most viewed</option><option value="newest">Newest</option><option value="oldest">Oldest</option></select></label>
      </form>
      <div class="impact-table-wrap">
        <table class="impact-table">
          <thead><tr><th>Published</th><th>Article</th><th>Platform</th><th>Article views</th><th>Impressions</th><th>Reactions</th><th>Comments</th></tr></thead>
          <tbody id="impact-rows">
{rows}
          </tbody>
        </table>
        <p class="impact-empty" id="impact-empty" hidden>No measured articles match these filters.</p>
      </div>
    </section>
  </main>
  <footer class="page-footer"><span>Generated {generated_at[:10]} from dated platform observations.</span><a href="./">Article archive</a><a href="https://www.linkedin.com/in/franckpachot/">LinkedIn</a></footer>
  <script>
    (() => {{
      const body = document.getElementById('impact-rows');
      const rows = [...body.querySelectorAll('tr')];
      const search = document.getElementById('impact-search');
      const source = document.getElementById('impact-source');
      const sort = document.getElementById('impact-sort');
      const count = document.getElementById('impact-count');
      const empty = document.getElementById('impact-empty');
      function render() {{
        const query = search.value.trim().toLowerCase();
        const visible = rows.filter(row => (!query || row.dataset.search.includes(query)) && (!source.value || row.dataset.source === source.value));
        visible.sort((left, right) => sort.value === 'views' ? Number(right.dataset.views) - Number(left.dataset.views) : sort.value === 'oldest' ? left.dataset.date.localeCompare(right.dataset.date) : right.dataset.date.localeCompare(left.dataset.date));
        rows.forEach(row => row.hidden = true);
        visible.forEach(row => {{ row.hidden = false; body.appendChild(row); }});
        count.textContent = visible.length.toLocaleString();
        empty.hidden = visible.length !== 0;
      }}
      search.addEventListener('input', render);
      source.addEventListener('change', render);
      sort.addEventListener('change', render);
      render();
    }})();
  </script>
</body>
</html>
'''


def write_impact_page(root: Path) -> int:
    publications = latest_observations(root)
    source_counts = archived_source_counts(root)
    (root / "impact.html").write_text(
        build_document(publications, source_counts), encoding="utf-8"
    )
    return len(publications)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    count = write_impact_page(args.root.resolve())
    print(f"Wrote impact.html with {count} measured publications")


if __name__ == "__main__":
    main()
