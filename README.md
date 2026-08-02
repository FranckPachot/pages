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

Then open `index.html` directly or serve the repository with any static HTTP server.
