#!/usr/bin/env python3
"""Lädt CSS/JS/Bilder aus gespeichertem HTML nach (Extension speichert nur HTML)."""

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
from urllib.parse import quote, urljoin, urlparse

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites"
COOKIES_FILE = ROOT / "cookies.json"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

ASSET_HOSTS = ("louisvuitton.com",)
SKIP_SCHEMES = ("data:", "blob:", "javascript:", "chrome-extension:")


def load_cookie_header() -> str:
    if not COOKIES_FILE.exists():
        return ""
    raw = json.loads(COOKIES_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return ""
    parts = []
    for c in raw:
        dom = c.get("domain", "")
        if "louisvuitton" not in dom:
            continue
        parts.append(f"{c['name']}={c['value']}")
    return "; ".join(parts)


def safe_name(url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    path = urlparse(url).path
    base = Path(path).name or "asset"
    base = re.sub(r"[^\w.\-]", "_", base)[:60]
    return f"{base}_{h}"


def normalize_url(url: str, page_url: str = "") -> Optional[str]:
    url = unescape(url.strip()).strip('"\'')
    if not url or url.startswith(SKIP_SCHEMES):
        return None
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = urljoin("https://de.louisvuitton.com", url)
    if not url.startswith("http"):
        return None
    host = urlparse(url).netloc.lower()
    if not any(h in host for h in ASSET_HOSTS):
        return None
    return url.split("#")[0]


def extract_urls(html: str, page_url: str = "") -> Dict[str, Set[str]]:
    found: Dict[str, Set[str]] = {"css": set(), "js": set(), "imgs": set()}

    for m in re.finditer(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', html, re.I):
        tag = m.group(0)
        hm = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
        if hm:
            u = normalize_url(hm.group(1), page_url)
            if u:
                found["css"].add(u)

    for m in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.I):
        u = normalize_url(m.group(1), page_url)
        if u:
            found["js"].add(u)

    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I):
        u = normalize_url(m.group(1), page_url)
        if u:
            found["imgs"].add(u)

    for m in re.finditer(r'\bsrcset=["\']([^"\']+)["\']', html, re.I):
        for part in m.group(1).split(","):
            u = normalize_url(part.strip().split()[0], page_url)
            if u:
                found["imgs"].add(u)

    for m in re.finditer(r'url\(([^)]+)\)', html, re.I):
        raw = m.group(1).strip().strip('"\'')
        u = normalize_url(raw, page_url)
        if u and any(x in u for x in ("/images/", ".jpg", ".png", ".webp", ".gif", ".svg")):
            found["imgs"].add(u)

    for m in re.finditer(r'https://de\.louisvuitton\.com/images[^\s"\'<>]+', html):
        u = normalize_url(m.group(0), page_url)
        if u:
            found["imgs"].add(u)

    for m in re.finditer(r'"/images/[^"\s<>]+"', html):
        u = normalize_url(m.group(0).strip('"'), page_url)
        if u:
            found["imgs"].add(u)

    return found


def guess_subdir(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.endswith(".css") or "/css" in path:
        return "css"
    if path.endswith(".js") or "/js" in path or path.endswith(".bin"):
        return "js"
    return "imgs"


def download_file(url: str, dest: Path, cookie: str) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    parsed = urlparse(url)
    safe_path = quote(parsed.path, safe="/%")
    safe_query = quote(parsed.query, safe="=&%") if parsed.query else ""
    safe_url = f"{parsed.scheme}://{parsed.netloc}{safe_path}"
    if safe_query:
        safe_url += f"?{safe_query}"
    req = urllib.request.Request(
        safe_url,
        headers={
            "User-Agent": UA,
            "Cookie": cookie,
            "Referer": "https://de.louisvuitton.com/",
            "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
        if len(data) < 50:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except (urllib.error.URLError, OSError, TimeoutError, UnicodeError):
        return False


def process_page(page_dir: Path, cookie: str, delay: float) -> Dict[str, int]:
    html_path = page_dir / "index.html"
    if not html_path.is_file() or html_path.stat().st_size < 50_000:
        return {"skipped": 1}

    html = html_path.read_text(encoding="utf-8", errors="ignore")
    status = (page_dir / "status.txt").read_text(encoding="utf-8", errors="ignore") if (page_dir / "status.txt").exists() else ""
    page_url = ""
    for line in status.splitlines():
        if line.startswith("url="):
            page_url = line[4:].strip()
            break

    urls = extract_urls(html, page_url)
    asset_map: Dict[str, str] = {}
    stats = {"css": 0, "js": 0, "imgs": 0, "fail": 0}

    all_items: List[tuple[str, str]] = []
    for sub, us in urls.items():
        for u in us:
            all_items.append((sub, u))

    for sub, url in sorted(all_items, key=lambda x: x[1]):
        ext = Path(urlparse(url).path).suffix.split("?")[0]
        if not ext or len(ext) > 6:
            ext = ".bin"
        local = f"{sub}/{safe_name(url)}{ext}"
        dest = page_dir / local
        if download_file(url, dest, cookie):
            asset_map[url] = local
            stats[sub] += 1
        else:
            stats["fail"] += 1
        if delay:
            time.sleep(delay)

    # auch ohne Query-Varianten ersetzen
    for remote, local in sorted(asset_map.items(), key=lambda x: -len(x[0])):
        html = html.replace(remote, local)
        html = html.replace(remote.replace("&", "&amp;"), local)

    html_path.write_text(html, encoding="utf-8")
    return stats


def iter_page_dirs(target: Optional[str]) -> Iterable[Path]:
    if target:
        p = SITES / target if not target.startswith("sites/") else ROOT / target
        if p.is_dir() and (p / "index.html").exists():
            yield p
        return
    for html in sorted(SITES.rglob("index.html")):
        if html.parent == SITES:
            continue
        yield html.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Assets für gespeicherte HTML-Seiten nachladen")
    parser.add_argument("--target", help="z.B. herren/ready-to-wear/vollstandige-ready-to-wear")
    parser.add_argument("--products-only", action="store_true")
    parser.add_argument("--delay", type=float, default=0.15, help="Pause zwischen Downloads")
    args = parser.parse_args()

    cookie = load_cookie_header()
    if not cookie:
        print("WARN: cookies.json fehlt — Download kann blockiert werden")

    dirs = list(iter_page_dirs(args.target))
    if args.products_only:
        dirs = [d for d in dirs if d.parts[-2] == "produkte" if len(d.parts) >= 2]
        dirs = [d for d in dirs if "produkte" in d.parts]

    print(f"Verarbeite {len(dirs)} Seiten …")
    totals = {"css": 0, "js": 0, "imgs": 0, "fail": 0, "pages": 0}

    for i, page_dir in enumerate(dirs, 1):
        rel = page_dir.relative_to(SITES)
        print(f"[{i}/{len(dirs)}] {rel}")
        stats = process_page(page_dir, cookie, args.delay)
        if stats.get("skipped"):
            print("  übersprungen")
            continue
        totals["pages"] += 1
        for k in ("css", "js", "imgs", "fail"):
            totals[k] += stats.get(k, 0)
        print(f"  css={stats.get('css',0)} js={stats.get('js',0)} imgs={stats.get('imgs',0)} fail={stats.get('fail',0)}")

    print(f"\nFertig: {totals['pages']} Seiten · imgs={totals['imgs']} css={totals['css']} js={totals['js']} fail={totals['fail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
