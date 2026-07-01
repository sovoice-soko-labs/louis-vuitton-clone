#!/usr/bin/env python3
"""HTML für Offline/Replit reparieren: Pfade, Bilder, Links."""

import argparse
import re
from html import unescape
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites"
LV = "https://de.louisvuitton.com"

PRODUCT_HREF = re.compile(
    r'href=(["\'])/deu-de/produkte/[^"\']+/([A-Z0-9]{5,8})\1', re.I
)
CATEGORY_HREF = re.compile(
    r'href=(["\'])/deu-de/(herren/[^"\']+)["\']', re.I
)
ROOT_PATH = re.compile(
    r'((?:src|href|imagesrcset|srcset|data-src)=)(["\'])(/[^"\']+)["\']', re.I
)
NUXT_SCRIPT = re.compile(
    r'<script[^>]+src=(["\'])/_nuxt/[^"\']+["\'][^>]*>\s*</script>',
    re.I,
)
MODULE_PRELOAD = re.compile(
    r'<link[^>]+rel=(["\'])modulepreload\1[^>]*>', re.I
)
SHORT_PRODUCT_URL = re.compile(
    r"https?://(?:de|en|www)\.louisvuitton\.com/produkte/([A-Z0-9]{5,8})/?",
    re.I,
)
LONG_PRODUCT_URL = re.compile(
    r"https?://(?:de|en|www)\.louisvuitton\.com/deu-de/produkte/[^\"'\s<>]+/([A-Z0-9]{5,8})",
    re.I,
)
FULL_LV_IMAGE = re.compile(
    r"https?://(?:de|en|www)\.louisvuitton\.com(/images/[^\"'\s<>\)]+)",
    re.I,
)
PRODUCT_CODE = re.compile(r"--([A-Z0-9]{6,})[_\-.]")

IMAGE_INDEX: Dict[str, Tuple[str, str]] = {}
SKU_THUMB: Dict[str, str] = {}


def _norm_name(name: str) -> str:
    return unquote(name).replace("%20", " ").replace("_", " ").lower()


def build_image_index() -> None:
    """Index aller heruntergeladenen Bilder für Kategorie- und Querverweise."""
    global IMAGE_INDEX, SKU_THUMB
    IMAGE_INDEX = {}
    SKU_THUMB = {}

    produkte = SITES / "produkte"
    if not produkte.is_dir():
        return

    for prod_dir in sorted(produkte.iterdir()):
        if not prod_dir.is_dir():
            continue
        sku = prod_dir.name
        imgs = prod_dir / "imgs"
        if not imgs.is_dir():
            continue

        thumb: Optional[str] = None
        for f in sorted(imgs.iterdir()):
            if not f.is_file():
                continue
            web = f"/produkte/{sku}/imgs/{f.name}"
            IMAGE_INDEX[f.name.lower()] = (sku, f.name)
            stem = f.stem.lower()
            if len(stem) > 20:
                IMAGE_INDEX[stem[:40]] = (sku, f.name)
            for code in PRODUCT_CODE.findall(f.name):
                IMAGE_INDEX[code.lower()] = (sku, f.name)
            if thumb is None and (
                "front" in f.name.lower() or "_pm2_" in f.name.lower()
            ):
                thumb = web
        if thumb:
            SKU_THUMB[sku] = thumb


def local_img_exists(page_dir: Path, url_path: str) -> Optional[Tuple[str, str]]:
    """Map /images/... zu (sku, dateiname) wenn vorhanden."""
    tail = _norm_name(Path(url_path).name.split("?")[0])
    imgs = page_dir / "imgs"
    if imgs.is_dir():
        for f in imgs.iterdir():
            if not f.is_file():
                continue
            fn = _norm_name(f.name)
            if tail in fn or fn.startswith(tail[:24]):
                return page_dir.name, f.name

    for key, (sku, fname) in IMAGE_INDEX.items():
        if tail in key or key in tail:
            return sku, fname
        if len(tail) > 16 and tail[:24] in key:
            return sku, fname

    codes = PRODUCT_CODE.findall(unquote(url_path))
    for code in codes:
        hit = IMAGE_INDEX.get(code.lower())
        if hit:
            return hit

    return None


def web_img_path(page_dir: Path, sku: str, filename: str) -> str:
    if page_dir.name == sku:
        return f"imgs/{filename}"
    return f"/produkte/{sku}/imgs/{filename}"


def resolve_image_url(url: str, page_dir: Path) -> Optional[str]:
    path = url
    if url.startswith("http"):
        m = FULL_LV_IMAGE.match(url)
        if not m:
            return None
        path = m.group(1)
    if not path.startswith("/images/"):
        return None
    hit = local_img_exists(page_dir, path)
    if not hit:
        return None
    sku, fname = hit
    return web_img_path(page_dir, sku, fname)


def resolve_any_url(url: str, page_dir: Path) -> str:
    if url.startswith("http") and "louisvuitton.com" in url:
        loc = resolve_image_url(url, page_dir)
        if loc:
            return loc
        if "/images/" not in url:
            return url
        return url
    if url.startswith("/images/"):
        loc = resolve_image_url(url, page_dir)
        return loc or (LV + url)
    return url


def rewrite_product_urls(html: str) -> str:
    html = SHORT_PRODUCT_URL.sub(r"/produkte/\1/", html)
    html = LONG_PRODUCT_URL.sub(r"/produkte/\1/", html)
    return html


def rewrite_lv_images(html: str, page_dir: Path) -> str:
    def repl(m: re.Match) -> str:
        loc = resolve_image_url(m.group(0), page_dir)
        return loc if loc else m.group(0)

    return FULL_LV_IMAGE.sub(repl, html)


def rewrite_root_paths(html: str, page_dir: Path) -> str:
    def repl(m: re.Match) -> str:
        attr, q, path = m.group(1), m.group(2), m.group(3)
        if path.startswith("//"):
            return m.group(0)
        if path.startswith("/images/") or "/images/" in path:
            hit = local_img_exists(page_dir, path)
            if hit:
                sku, fname = hit
                return f"{attr}{q}{web_img_path(page_dir, sku, fname)}{q}"
            return f"{attr}{q}{LV}{path}{q}"
        if path.startswith("/deu-de/"):
            rest = path[len("/deu-de/") :]
            if rest.startswith("produkte/"):
                sku = rest.rstrip("/").split("/")[-1]
                return f"{attr}{q}/produkte/{sku}/{q}"
            return f"{attr}{q}/{rest}{q}"
        if path.startswith("/_nuxt/") or path.startswith("/deu-de/ruxit"):
            return ""
        if path.startswith("/produkte/"):
            return m.group(0)
        return f"{attr}{q}{LV}{path}{q}"

    return ROOT_PATH.sub(repl, html)


def fix_srcset_attr(html: str, page_dir: Path) -> str:
    def fix_value(raw: str) -> str:
        raw = unescape(raw)
        parts = []
        for bit in raw.split(","):
            bit = bit.strip()
            if not bit:
                continue
            seg = bit.split()
            seg[0] = resolve_any_url(seg[0], page_dir)
            parts.append(" ".join(seg))
        return " , ".join(parts)

    def repl(m: re.Match) -> str:
        return f"{m.group(1)}={m.group(2)}{fix_value(m.group(3))}{m.group(2)}"

    html = re.sub(
        r'\b(srcset|imagesrcset)=(["\'])([^"\']+)\2',
        repl,
        html,
        flags=re.I,
    )
    return html


def inject_offline_styles(html: str) -> str:
    inject = (
        "<style>"
        ".lv-page-loader,#__nuxt .lv-page-loader{display:none!important}"
        ".ucm-popin,.ucm-pushpop,.ucm-push-view,#onetrust-consent-sdk"
        "{display:none!important;visibility:hidden!important}"
        "body{overflow:auto!important}"
        "</style>"
    )
    if inject in html:
        return html
    if "</head>" in html:
        return html.replace("</head>", inject + "</head>", 1)
    return inject + html


def fix_file(path: Path) -> bool:
    html = path.read_text(encoding="utf-8", errors="ignore")
    orig = html
    page_dir = path.parent

    html = rewrite_product_urls(html)
    html = PRODUCT_HREF.sub(r"href=\1/produkte/\2/\1", html)
    html = CATEGORY_HREF.sub(r"href=\1/\2\1", html)
    html = rewrite_root_paths(html, page_dir)
    html = rewrite_lv_images(html, page_dir)
    html = fix_srcset_attr(html, page_dir)

    html = NUXT_SCRIPT.sub("", html)
    html = MODULE_PRELOAD.sub("", html)
    html = inject_offline_styles(html)

    if html != orig:
        path.write_text(html, encoding="utf-8")
        return True
    return False


def iter_pages(target: Optional[str]) -> Iterable[Path]:
    if target:
        p = SITES / target if not target.startswith("sites/") else ROOT / target
        if (p / "index.html").is_file():
            yield p / "index.html"
        return
    for html in sorted(SITES.rglob("index.html")):
        if html.parent == SITES:
            continue
        yield html


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline-HTML für Replit fixen")
    parser.add_argument("--target")
    args = parser.parse_args()
    build_image_index()
    print(f"Bild-Index: {len(IMAGE_INDEX)} Einträge, {len(SKU_THUMB)} Thumbnails")
    changed = 0
    for p in iter_pages(args.target):
        if fix_file(p):
            changed += 1
            print(f"  fixed {p.relative_to(SITES)}")
    print(f"Fertig: {changed} Dateien angepasst")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
