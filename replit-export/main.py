#!/usr/bin/env python3
"""Louis Vuitton RTW — Offline-Klon für Replit."""
import os
import socketserver
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

PORT = int(os.environ.get("PORT", "8080"))
SITES = Path(__file__).resolve().parent / "sites"
os.chdir(SITES)


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **getattr(SimpleHTTPRequestHandler, "extensions_map", {}),
        ".webp": "image/webp",
        ".woff2": "font/woff2",
    }

    def translate_path(self, path):
        path = unquote(path.split("?", 1)[0])
        if path in ("", "/"):
            return str(SITES / "index.html")
        local = SITES / path.lstrip("/")
        if local.is_dir():
            idx = local / "index.html"
            if idx.is_file():
                return str(idx)
        return str(local)

    def end_headers(self):
        self.send_header("Cache-Control", "public, max-age=3600")
        super().end_headers()


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"LV RTW Klon: http://0.0.0.0:{PORT}/")
        print(f"Kategorie: http://0.0.0.0:{PORT}/herren/ready-to-wear/vollstandige-ready-to-wear/")
        httpd.serve_forever()
