#!/usr/bin/env python3
"""Louis Vuitton RTW — Offline-Klon für Replit."""
import os
import socketserver
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

PORT = int(os.environ.get("PORT", "8080"))
ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites"
CATEGORY = "/herren/ready-to-wear/vollstandige-ready-to-wear/"
os.chdir(SITES)


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **getattr(SimpleHTTPRequestHandler, "extensions_map", {}),
        ".webp": "image/webp",
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".bin": "application/octet-stream",
        ".svg": "image/svg+xml",
    }

    def log_message(self, fmt, *args):
        if args and str(args[0]).startswith("GET /_nuxt"):
            return
        super().log_message(fmt, *args)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])
        if path in ("", "/"):
            self.send_response(302)
            self.send_header("Location", CATEGORY)
            self.end_headers()
            return
        if path.startswith("/_nuxt/") or path.startswith("/deu-de/"):
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def translate_path(self, path):
        path = unquote(path.split("?", 1)[0])
        local = SITES / path.lstrip("/")
        if local.is_dir():
            idx = local / "index.html"
            if idx.is_file():
                return str(idx)
        return str(local)

    def end_headers(self):
        self.send_header("Cache-Control", "public, max-age=3600")
        super().end_headers()


class ThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with ThreadingServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"LV RTW Klon: http://0.0.0.0:{PORT}{CATEGORY}")
        httpd.serve_forever()
