#!/usr/bin/env python3
"""Replit-Export: sites + Server + Produktindex."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPORT = ROOT / "replit-export"
SITES = ROOT / "sites"
QUEUE = ROOT / "products_queue.json"

MAIN_PY = '''#!/usr/bin/env python3
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
'''

REPLIT = """run = "python main.py"
modules = ["python-3.11"]

[nix]
channel = "stable-24_05"

[deployment]
run = ["python", "main.py"]
deploymentTarget = "cloudrun"

[[ports]]
localPort = 8080
externalPort = 80
"""

README = """# Louis Vuitton — Herren Ready-to-Wear (Offline)

Offline-Klon der LV Ready-to-Wear-Kategorie inkl. **183 Produktseiten** für Replit.

## Replit starten

1. Repo **louis-vuitton-clone** importieren (Root = Repo-Root mit `main.py`)
2. **Run** klicken — Port 8080 wird automatisch geöffnet
3. Startseite leitet weiter zu `/herren/ready-to-wear/vollstandige-ready-to-wear/`

Alternativ nur `replit-export/` als eigenes Repl nutzen.

## Lokal

```bash
python main.py
# → http://localhost:8080/
```

## Struktur

- `sites/` — HTML, Bilder, CSS, JS
- `sites/index.html` — Übersicht
- `products.json` — SKU-Liste mit URLs
- `main.py` — Static Server

## Hinweis

Produktbilder stammen vom Live-Site-Crawl. Nur für private/offline Demos.
"""


def build_index_html(products: list) -> str:
    items = [
        '<li><a href="/homepage/">Homepage <span class="tag">Start</span></a></li>',
        '<li><a href="/herren/ready-to-wear/vollstandige-ready-to-wear/">'
        "Herren Ready-to-Wear — alle Produkte <span class=\"tag\">183</span></a></li>",
        '<li><a href="/herren/ready-to-wear/">Ready-to-Wear Übersicht</a></li>',
    ]
    for p in products:
        sku = p["sku"]
        name = p.get("name", sku)
        if not p.get("name"):
            name = sku
        items.append(
            f'<li><a href="/produkte/{sku}/">{name} '
            f'<span class="tag">{sku}</span></a></li>'
        )
    body = "\n    ".join(items)
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Louis Vuitton RTW — Offline</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      max-width: 800px;
      margin: 2rem auto;
      padding: 0 1.5rem;
      color: #111;
      line-height: 1.5;
    }}
    h1 {{ font-weight: 400; letter-spacing: 0.06em; font-size: 1.4rem; }}
    p.sub {{ color: #666; margin-bottom: 1.5rem; }}
    ul {{ list-style: none; padding: 0; margin: 0; }}
    li {{ border-top: 1px solid #e5e5e5; }}
    a {{ display: block; padding: 0.75rem 0; color: #111; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .tag {{ float: right; color: #888; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <h1>LOUIS VUITTON — Ready-to-Wear</h1>
  <p class="sub">Offline-Klon · {len(products)} Produkte</p>
  <ul>
    {body}
  </ul>
</body>
</html>
"""


def product_name_from_html(sku: str) -> str:
    html = SITES / "produkte" / sku / "index.html"
    if not html.is_file():
        return sku
    text = html.read_text(encoding="utf-8", errors="ignore")[:8000]
    import re

    m = re.search(r"<title>([^<]+)</title>", text, re.I)
    if m:
        t = m.group(1).split("|")[0].strip()
        if t and "LOUIS VUITTON" not in t.upper()[:5]:
            return t[:80]
    return sku


def load_products() -> list:
    """Alle gespeicherten Produktseiten aus sites/produkte/ laden."""
    queue_urls = {}
    if QUEUE.is_file():
        data = json.loads(QUEUE.read_text(encoding="utf-8"))
        for p in data.get("products", []):
            queue_urls[p["sku"]] = p.get("url", "")

    products = []
    produkte = SITES / "produkte"
    if produkte.is_dir():
        for d in sorted(produkte.iterdir()):
            if not d.is_dir() or not (d / "index.html").is_file():
                continue
            sku = d.name
            products.append({
                "sku": sku,
                "url": queue_urls.get(sku, ""),
                "name": product_name_from_html(sku),
                "path": f"/produkte/{sku}/",
            })
    return products


def main() -> None:
    if EXPORT.exists():
        shutil.rmtree(EXPORT)
    EXPORT.mkdir()

    products = load_products()

    print("HTML für Offline/Replit reparieren …")
    subprocess.run([sys.executable, str(ROOT / "fix_offline_html.py")], cwd=str(ROOT), check=False)

    print("Kopiere sites/ …")
    shutil.copytree(SITES, EXPORT / "sites", ignore=shutil.ignore_patterns(".DS_Store"))

    (EXPORT / "sites" / "index.html").write_text(build_index_html(products), encoding="utf-8")
    (EXPORT / "main.py").write_text(MAIN_PY, encoding="utf-8")
    (EXPORT / ".replit").write_text(REPLIT, encoding="utf-8")
    (EXPORT / "README.md").write_text(README, encoding="utf-8")
    (EXPORT / "products.json").write_text(
        json.dumps({"total": len(products), "products": products}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (EXPORT / ".gitignore").write_text("__pycache__/\n.DS_Store\n", encoding="utf-8")

    size_mb = sum(f.stat().st_size for f in EXPORT.rglob("*") if f.is_file()) / (1024 * 1024)
    print(f"Export: {EXPORT} ({size_mb:.0f} MB, {len(products)} Produkte)")


if __name__ == "__main__":
    main()
