#!/usr/bin/env python3
"""Receive sanitized LinkedIn article snapshots from an authenticated browser."""

from __future__ import annotations

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from archive_articles import linkedin_manifest_entry, write_json_atomic


class SnapshotServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], root: Path) -> None:
        super().__init__(address, SnapshotHandler)
        self.root = root


class SnapshotHandler(BaseHTTPRequestHandler):
    server: SnapshotServer

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 5_000_000:
                raise ValueError("Invalid snapshot size")
            detail: dict[str, Any] = json.loads(self.rfile.read(length))
            article_id = detail.get("id", "")
            if not re.fullmatch(r"[a-z0-9-]+", article_id):
                raise ValueError("Invalid article ID")
            path = self.server.root / "linkedin" / "articles" / f"{article_id}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            linkedin_manifest_entry(self.server.root, path, detail)
            write_json_atomic(path, detail)
            self.send_response(201)
            self.end_headers()
            self.wfile.write(b"saved\n")
            print(f"LinkedIn: {detail['title']}")
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"{error}\n".encode())

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = SnapshotServer(("127.0.0.1", args.port), args.root.resolve())
    print(f"Listening on http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()