# Franck Pachot's article archive

This repository preserves articles published across several platforms:

- [DBI Services](https://www.dbi-services.com/blog/) WordPress API snapshots filtered by the exact `By Franck Pachot` article heading; the older HTML exports remain under `2013-2018/`
- [Medium](https://franckpachot.github.io/pages/2018-medium/posts) account export
- [Dev.to](https://dev.to/franckpachot) API snapshots, including source Markdown and rendered HTML when supplied by the API
- [Yugabyte](https://www.yugabyte.com/blog/author/fpachot/) WordPress API snapshots, including rendered article content
- [Microsoft Tech Community](https://techcommunity.microsoft.com/users/franckpachot/3595257) HTML snapshots verified against the article's structured author metadata
- [Databases at CERN](https://db-blog.web.cern.ch/users/franck-pachot) Drupal JSON:API snapshots, including rendered article content
- [LinkedIn Articles](https://www.linkedin.com/in/franckpachot/recent-activity/articles/) sanitized JSON snapshots captured from article pages in an authenticated browser; no account or session data is stored

`archive-manifest.json` is the unified, machine-readable inventory. Each entry records its source, stable source ID, title, publication date, canonical URL, local archive path, and tags when available. The original exports remain unchanged.

## Refresh the archive

Python 3 is the only prerequisite. From the repository root, run:

```shell
python util/archive_articles.py
```

The command discovers current DBI Services, Dev.to, Yugabyte, Microsoft Tech Community, and CERN articles; rescans the local Medium export; downloads only snapshots that are not already present; and regenerates the manifest.

LinkedIn blocks anonymous article discovery and its activity feed omits older articles. Its snapshots are therefore captured separately through `util/capture_linkedin.py`, a localhost-only receiver for article metadata and body HTML extracted in an authenticated browser. The regular archive command inventories those local snapshots, including in `--offline` mode.

Use `--refresh-dbi`, `--refresh-devto`, `--refresh-yugabyte`, `--refresh-techcommunity`, or `--refresh-cern` to replace existing snapshots from one source. The corresponding `--skip-*` options avoid contacting that source, while `--offline` rebuilds the manifest entirely from local snapshots.

## Browse the publication index

The searchable index at the [site root](index.html) groups all publications by year, source, database, version, category, and tag. It also provides full-text search across titles, summaries, tags, and archived article text. The generated root page includes crawlable recent article links and structured data; `sitemap.xml` and `robots.txt` support search-engine discovery.

Regenerate its browser catalog after refreshing the archive:

```shell
python util/build_publication_map.py
```

This also rebuilds `impact.html` from the latest dated observation for each publication under `impact/<source>/`. Platform metrics remain separate: article views are not inferred from impressions, reactions, or public counters.

Authenticated DEV metrics can be refreshed without putting an API key in the repository or command history. Set `BLOG_ARCHIVE_DEVTO_API_KEY` directly in the process environment, then run:

```shell
python util/collect_publication_impact.py --all-devto
```

LinkedIn metrics require an authenticated author browser session and are stored as dated snapshots under `impact/linkedin/`. The unattended daily workflow rebuilds the impact page from available observations but does not access authenticated analytics.

Then open `index.html` or `impact.html` directly, or serve the repository with any static HTTP server.

## Daily publication discovery

The `Daily publication refresh` GitHub Actions workflow runs every day at 06:17 UTC and can also be started manually. It checks the public APIs and feeds supported by `util/archive_articles.py`, rebuilds the publication index without retagging unrelated HTML pages, and opens or updates a single review pull request only when files change. It never posts, replies, reacts, follows, or changes anything on a social platform.

The workflow discovers publications from DBI Services, Dev.to, Yugabyte, Microsoft Tech Community, CERN, and Developpez. Medium and LinkedIn remain local or authenticated imports, so they are inventoried but cannot be discovered by the unattended job. Review the pull request before merging, especially when a new article needs a curated description.

## Build the agent knowledge base

`db-skills.md` combines the curated database field manuals with an exhaustive, deduplicated registry of archived publications. The workspace skill at `.github/skills/database-experience/SKILL.md` tells agents when and how to consult it.

Regenerate it after refreshing publications or changing a minibook:

```shell
python3.13 util/generate_db_skills.py
```

The companion [database lab guide](how-to-build-a-db-lab.md) turns the publication method into reproducible PostgreSQL, Oracle Database, YugabyteDB, and MongoDB experiments with shared fixtures and source links.
