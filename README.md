# Franck Pachot's article archive

This repository preserves articles published across several platforms:

- [DBI Services](https://franckpachot.github.io/pages/2013-2018/) exports, including the comments available when they were archived
- [Medium](https://franckpachot.github.io/pages/2018-medium/posts) account export
- [Dev.to](https://dev.to/franckpachot) API snapshots, including source Markdown and rendered HTML when supplied by the API
- [Yugabyte](https://www.yugabyte.com/blog/author/fpachot/) WordPress API snapshots, including rendered article content
- [Microsoft Tech Community](https://techcommunity.microsoft.com/users/franckpachot/3595257) HTML snapshots verified against the article's structured author metadata

`archive-manifest.json` is the unified, machine-readable inventory. Each entry records its source, stable source ID, title, publication date, canonical URL, local archive path, and tags when available. The original exports remain unchanged.

## Refresh the archive

Python 3 is the only prerequisite. From the repository root, run:

```shell
python util/archive_articles.py
```

The command rescans the local DBI Services and Medium exports; discovers current Dev.to, Yugabyte, and Microsoft Tech Community articles; downloads only snapshots that are not already present; and regenerates the manifest.

Use `--refresh-devto`, `--refresh-yugabyte`, or `--refresh-techcommunity` to replace existing snapshots from one source. The corresponding `--skip-*` options avoid contacting that source, while `--offline` rebuilds the manifest entirely from local snapshots.

## Browse the publication map

The searchable map in [`home/`](home/) groups all publications by year, source, database, version, category, and tag. It also provides full-text search across titles, summaries, tags, and archived article text.

Regenerate its browser catalog after refreshing the archive:

```shell
python util/build_publication_map.py
```

Then open `home/index.html` directly or serve the repository with any static HTTP server.
