#!/usr/bin/env python3
"""Regression checks for the generated publication RSS feed."""

import tempfile
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

from build_publication_map import ATOM_NAMESPACE, RSS_ITEM_LIMIT, SITE_URL, write_rss


def main() -> None:
    publications = [
        {
            "id": f"dev.to:{number}",
            "title": f"Article {number}",
            "date": (date(2026, 1, 1) + timedelta(days=number - 1)).isoformat(),
            "canonical_url": f"https://dev.to/example/article-{number}",
            "summary": f"Summary {number}",
            "source": "Dev.to",
            "tags": ["postgres", "database"],
        }
        for number in range(1, RSS_ITEM_LIMIT + 2)
    ]

    with tempfile.TemporaryDirectory() as temporary_directory:
        output = Path(temporary_directory) / "rss.xml"
        write_rss(output, {"publications": publications})
        root = ET.parse(output).getroot()
        channel = root.find("channel")
        assert root.tag == "rss" and root.get("version") == "2.0"
        assert channel is not None
        assert channel.findtext("link") == SITE_URL
        atom_link = channel.find(f"{{{ATOM_NAMESPACE}}}link")
        assert atom_link is not None
        assert atom_link.get("href") == f"{SITE_URL}rss.xml"
        assert atom_link.get("rel") == "self"
        items = channel.findall("item")
        assert len(items) == RSS_ITEM_LIMIT
        assert items[0].findtext("title") == f"Article {RSS_ITEM_LIMIT + 1}"
        assert items[-1].findtext("title") == "Article 2"
        assert items[0].findtext("guid") == items[0].findtext("link")
        assert items[0].find("guid").get("isPermaLink") == "true"
        assert items[0].findtext("pubDate") == "Fri, 20 Feb 2026 00:00:00 +0000"
        assert [category.text for category in items[0].findall("category")] == [
            "Dev.to",
            "postgres",
            "database",
        ]


if __name__ == "__main__":
    main()