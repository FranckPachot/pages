#!/usr/bin/env python3
"""Regression checks for readable CERN archives and Medium source links."""

import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from build_publication_map import build_catalog, load_snapshot, write_sitemap
from render_cern_articles import render_cern_articles, without_cern_notice


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        canonical = "https://db-blog.web.cern.ch/blog/example/index-compression"
        article = {
            "source": "cern",
            "source_id": "150",
            "title": "Index compression",
            "published_at": "2018-11-30T12:44:53+00:00",
            "canonical_url": canonical,
            "archive_path": "cern/articles/150.json",
        }
        source = root / article["archive_path"]
        source.parent.mkdir(parents=True)
        body = (
            '<h2>Execution plan</h2><pre>SQL&gt; select count(*)  \n'
            '  from demo;\n|   2 | INDEX RANGE SCAN |   67 |</pre>'
            f'<a href="{canonical}#plan">Plan</a>'
            '<img src="http://db-blog-multimedia.web.cern.ch/images/plan.png">'
        )
        original = json.dumps({"attributes": {"body": {"processed": body}}})
        source.write_text(original, encoding="utf-8")
        asset = root / "cern" / "assets" / "plan.png"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 16)
        manifest = [article]
        for source_id, title in (("announcement", "Index compression"), ("citation", "A different article")):
            medium = {
                "source": "medium",
                "source_id": source_id,
                "title": title,
                "published_at": "2018-12-01T10:54:28Z",
                "canonical_url": f"https://medium.com/@example/{source_id}",
                "archive_path": f"2018-medium/posts/{source_id}.html",
            }
            path = root / medium["archive_path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f'<html><body><h1>{title}</h1><p>Original Medium text.</p>'
                f'<a href="{canonical.replace("https:", "http:")}/#context">Full test</a>'
                '</body></html>',
                encoding="utf-8",
            )
            manifest.append(medium)
        (root / "archive-manifest.json").write_text(
            json.dumps({"schema_version": 1, "articles": manifest}), encoding="utf-8"
        )

        assert render_cern_articles(root, manifest) == (1, 2)
        rendered = (root / "cern/rendered/150/index.html").read_text(encoding="utf-8")
        assert '<h2>Execution plan</h2><pre>SQL&gt; select count(*)\n  from demo;' in rendered
        assert 'src="../../assets/plan.png"' in rendered
        assert 'href="index.html#plan"' in rendered
        assert source.read_text(encoding="utf-8") == original
        announcement = root / manifest[1]["archive_path"]
        first = announcement.read_text(encoding="utf-8")
        assert 'href="../../cern/rendered/150/index.html"' in first
        assert without_cern_notice(first) == (
            '<html><body><h1>Index compression</h1><p>Original Medium text.</p>'
            f'<a href="{canonical.replace("https:", "http:")}/#context">Full test</a>'
            '</body></html>'
        )
        render_cern_articles(root, manifest)
        assert announcement.read_text(encoding="utf-8") == first
        assert "Read the full archived CERN article" not in load_snapshot(root, manifest[1])[0]

        catalog = build_catalog(root)
        publications = {item["id"]: item for item in catalog["publications"]}
        assert publications["cern:150"]["read_url"] == "cern/rendered/150/index.html"
        assert publications["medium:announcement"]["read_url"] == manifest[1]["canonical_url"]
        assert publications["medium:announcement"]["snapshot_url"] == manifest[1]["archive_path"]
        assert publications["medium:citation"]["read_url"] == manifest[2]["canonical_url"]
        assert publications["medium:citation"]["snapshot_url"] == manifest[2]["archive_path"]
        sitemap = root / "sitemap.xml"
        write_sitemap(sitemap, catalog, root)
        urls = [
            node.text
            for node in ET.parse(sitemap).findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        ]
        assert "https://franckpachot.github.io/pages/cern/rendered/150/index.html" in urls
        assert not any(url.endswith(".json") for url in urls)


if __name__ == "__main__":
    main()
