#!/usr/bin/env python3
"""Lädt Bilder/CSS/JS per Playwright-Request (Browser-Session, nicht urllib)."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright

from browser_clone import browser_executable, launch_args, load_cookies
from download_assets import extract_urls, safe_name

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites"
PROFILE_DIR = ROOT / ".opera-profile"
QUEUE = ROOT / "products_queue.json"
OPERA = Path("/Applications/Opera GX.app/Contents/MacOS/Opera")

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = window.chrome || { runtime: {} };
"""


async def pw_download_file(context, url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 200:
        return True
    try:
        resp = await context.request.get(
            url,
            timeout=45_000,
            headers={
                "Referer": "https://de.louisvuitton.com/",
                "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
            },
        )
        if not resp.ok:
            return False
        data = await resp.body()
        if len(data) < 80:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception:
        return False


async def process_page_browser(context, page_dir: Path, warmup_url: str) -> Dict[str, int]:
    html_path = page_dir / "index.html"
    if not html_path.is_file() or html_path.stat().st_size < 50_000:
        return {"skipped": 1}

    # Session mit echter Seite aufwärmen
    try:
        await context.request.get(warmup_url, timeout=90_000)
    except Exception:
        pass

    html = html_path.read_text(encoding="utf-8", errors="ignore")
    status = (page_dir / "status.txt").read_text(encoding="utf-8", errors="ignore") if (page_dir / "status.txt").exists() else ""
    page_url = warmup_url
    for line in status.splitlines():
        if line.startswith("url="):
            page_url = line[4:].strip()
            break

    urls = extract_urls(html, page_url)
    asset_map: Dict[str, str] = {}
    stats = {"css": 0, "js": 0, "imgs": 0, "fail": 0, "skip": 0}

    from urllib.parse import urlparse

    items: List[tuple] = []
    for sub, us in urls.items():
        for u in us:
            items.append((sub, u))

    for sub, url in sorted(items, key=lambda x: x[1]):
        ext = Path(urlparse(url).path).suffix.split("?")[0]
        if not ext or len(ext) > 6:
            ext = ".bin"
        local = f"{sub}/{safe_name(url)}{ext}"
        dest = page_dir / local
        if dest.exists() and dest.stat().st_size > 200:
            asset_map[url] = local
            stats["skip"] += 1
            continue
        if await pw_download_file(context, url, dest):
            asset_map[url] = local
            stats[sub] += 1
        else:
            stats["fail"] += 1
        await asyncio.sleep(0.05)

    for remote, local in sorted(asset_map.items(), key=lambda x: -len(x[0])):
        html = html.replace(remote, local)
        html = html.replace(remote.replace("&", "&amp;"), local)

    html_path.write_text(html, encoding="utf-8")
    return stats


def product_dirs(target: Optional[str], products_only: bool, limit: int) -> List[Path]:
    if target:
        p = SITES / target if not target.startswith("sites/") else ROOT / target
        return [p] if p.is_dir() else []
    dirs: List[Path] = []
    if products_only and QUEUE.is_file():
        data = json.loads(QUEUE.read_text(encoding="utf-8"))
        for item in data.get("products", []):
            d = SITES / "produkte" / item["sku"]
            if d.is_dir():
                dirs.append(d)
    else:
        extra = [
            SITES / "homepage",
            SITES / "herren/ready-to-wear/vollstandige-ready-to-wear",
            SITES / "herren/ready-to-wear",
        ]
        dirs.extend(p for p in extra if p.is_dir())
        dirs.extend(sorted((SITES / "produkte").iterdir()) if (SITES / "produkte").is_dir() else [])
    if limit:
        dirs = dirs[:limit]
    return dirs


def warmup_url_for(page_dir: Path) -> str:
    st = page_dir / "status.txt"
    if st.exists():
        for line in st.read_text(encoding="utf-8").splitlines():
            if line.startswith("url="):
                return line[4:].strip()
    return "https://de.louisvuitton.com/deu-de/homepage"


async def run(target: Optional[str], products_only: bool, limit: int, headed: bool) -> int:
    dirs = product_dirs(target, products_only, limit)
    if not dirs:
        print("Keine Seiten gefunden.")
        return 1

    print(f"Browser-Download für {len(dirs)} Seiten …")
    totals = {"css": 0, "js": 0, "imgs": 0, "fail": 0, "pages": 0}

    async with async_playwright() as p:
        exe = str(OPERA) if OPERA.is_file() else browser_executable()
        PROFILE_DIR.mkdir(exist_ok=True)
        ctx_opts = {
            "headless": not headed,
            "locale": "de-DE",
            "viewport": {"width": 1440, "height": 900},
            "args": launch_args(),
        }
        if exe:
            ctx_opts["executable_path"] = exe
        context = await p.chromium.launch_persistent_context(str(PROFILE_DIR), **ctx_opts)
        await context.add_init_script(STEALTH_JS)
        cookies = load_cookies()
        if cookies:
            await context.add_cookies(cookies)

        # Warmup echte Homepage im Browser
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            await page.goto(
                "https://de.louisvuitton.com/deu-de/homepage",
                wait_until="domcontentloaded",
                timeout=120_000,
            )
            await page.wait_for_timeout(4000)
        except Exception as exc:
            print(f"WARN Homepage-Warmup: {exc}")

        for i, page_dir in enumerate(dirs, 1):
            rel = page_dir.relative_to(SITES)
            print(f"[{i}/{len(dirs)}] {rel}")
            stats = await process_page_browser(context, page_dir, warmup_url_for(page_dir))
            if stats.get("skipped"):
                print("  übersprungen")
                continue
            totals["pages"] += 1
            for k in ("css", "js", "imgs", "fail"):
                totals[k] += stats.get(k, 0)
            print(
                f"  imgs={stats.get('imgs', 0)} js={stats.get('js', 0)} "
                f"fail={stats.get('fail', 0)} skip={stats.get('skip', 0)}"
            )

        await context.close()

    print(
        f"\nFertig: {totals['pages']} Seiten · "
        f"imgs={totals['imgs']} js={totals['js']} fail={totals['fail']}"
    )
    return 0 if totals["fail"] < totals["imgs"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Assets via Playwright-Browser laden")
    parser.add_argument("--target")
    parser.add_argument("--products-only", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--headed", action="store_true", default=True)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    headed = not args.headless
    return asyncio.run(run(args.target, args.products_only, args.limit, headed))


if __name__ == "__main__":
    raise SystemExit(main())
