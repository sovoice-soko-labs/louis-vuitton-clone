#!/usr/bin/env python3
"""
Lädt LV-Seiten inkl. Bilder/CSS/JS (Scrapling-Strategie: Browser + keine Resource-Blockade).

Scrapling selbst braucht Python 3.10+. Dieses Script nutzt dieselbe Idee:
  - echter Browser (Opera GX)
  - disable_resources=False → Bilder werden geladen
  - Responses abfangen und lokal speichern
  - Cookies aus cookies.json
"""

import argparse
import asyncio
import hashlib
import json
import re
import sys
from html import unescape
from pathlib import Path
from typing import Dict, Optional, Set, Tuple
from urllib.parse import urlparse

from playwright.async_api import BrowserContext, Page, async_playwright

from human_browse import human_go_to_target

from cdp_attach import connect_existing, discover_cdp_url

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites"
COOKIES_FILE = ROOT / "cookies.json"
OPERA_BIN = Path("/Applications/Opera GX.app/Contents/MacOS/Opera")
PROFILE_DIR = ROOT / ".opera-profile"
QUEUE = ROOT / "products_queue.json"
MIN_HTML = 50_000

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = window.chrome || { runtime: {} };
"""

LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
]


def safe_name(url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    base = Path(urlparse(url).path).name or "asset"
    base = re.sub(r"[^\w.\-]", "_", base)[:60]
    return f"{base}_{h}"


def load_pw_cookies() -> list:
    if not COOKIES_FILE.exists():
        return []
    raw = json.loads(COOKIES_FILE.read_text(encoding="utf-8"))
    out = []
    for c in raw:
        item = {
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".louisvuitton.com"),
            "path": c.get("path", "/"),
        }
        if c.get("secure"):
            item["secure"] = True
        ss = c.get("sameSite")
        if ss in ("Strict", "Lax", "None"):
            item["sameSite"] = ss
        elif ss == "no_restriction":
            item["sameSite"] = "None"
        out.append(item)
    return out


def asset_subdir(url: str, content_type: str) -> Optional[str]:
    ct = (content_type or "").lower()
    path = urlparse(url).path.lower()
    if "css" in ct or path.endswith(".css"):
        return "css"
    if "javascript" in ct or path.endswith(".js") or path.endswith(".bin"):
        return "js"
    if any(x in ct for x in ("image", "font", "webp", "svg")):
        return "imgs"
    if "/images/" in path or path.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg")):
        return "imgs"
    if "louisvuitton.com" in url and "/images/" in path:
        return "imgs"
    return None


class AssetCollector:
    def __init__(self, dest: Path):
        self.dest = dest
        self.map: Dict[str, str] = {}
        self.saved = 0
        self.seen: Set[str] = set()

    async def on_response(self, response) -> None:
        try:
            url = response.url
            if url in self.seen or not response.ok:
                return
            if "louisvuitton.com" not in url:
                return
            sub = asset_subdir(url, response.headers.get("content-type", ""))
            if not sub:
                return
            body = await response.body()
            if len(body) < 80:
                return
            ext = Path(urlparse(url).path).suffix.split("?")[0]
            if not ext or len(ext) > 6:
                ext = ".bin"
            local = f"{sub}/{safe_name(url)}{ext}"
            path = self.dest / local
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
                self.saved += 1
            self.map[url] = local
            self.seen.add(url)
        except Exception:
            pass


def rewrite_html(html: str, asset_map: Dict[str, str]) -> str:
    for remote, local in sorted(asset_map.items(), key=lambda x: -len(x[0])):
        html = html.replace(remote, local)
        html = html.replace(remote.replace("&", "&amp;"), local)
        enc = remote.replace("&", "&amp;")
        html = html.replace(enc, local)
    return html


async def save_fetched_page(
    page: Page, collector: AssetCollector, dest: Path, url: str
) -> bool:
    title = await page.title()
    html = await page.content()
    if len(html) < MIN_HTML or "Fehler aufgetreten" in title:
        print(f"  FEHLER: Seite unvollständig ({title[:50]}, {len(html)//1024} KB)")
        return False

    html = rewrite_html(html, collector.map)
    (dest / "index.html").write_text(html, encoding="utf-8")
    (dest / "status.txt").write_text(
        f"url={url}\ntitle={title}\nblocked=False\nsource=scrapling-fetch\nassets={collector.saved}\n",
        encoding="utf-8",
    )
    print(f"  OK: {collector.saved} Assets · {len(html)//1024} KB HTML")
    return True


def attach_collector(page: Page, dest: Path) -> AssetCollector:
    for sub in ("css", "js", "imgs"):
        (dest / sub).mkdir(exist_ok=True)
    collector = AssetCollector(dest)
    page.on("response", lambda r: asyncio.create_task(collector.on_response(r)))
    return collector


async def fetch_page_human(
    page: Page, url: str, rel_path: str, warmed: bool, from_existing: bool = False
) -> Tuple[bool, bool]:
    dest = SITES / rel_path
    dest.mkdir(parents=True, exist_ok=True)
    collector = attach_collector(page, dest)

    print(f"  Lade {url}")
    if from_existing:
        print("  Bestehender LV-Tab — Navigation ab Homepage …")
        warmed = True
    elif not warmed:
        from human_browse import human_google_to_lv

        print("  Menschlicher Weg: Google → LV → Homepage …")
        await human_google_to_lv(page)
        warmed = True

    await human_go_to_target(page, url)
    ok = await save_fetched_page(page, collector, dest, url)
    return ok, warmed


async def fetch_page_direct(context, url: str, rel_path: str) -> bool:
    dest = SITES / rel_path
    dest.mkdir(parents=True, exist_ok=True)
    page = await context.new_page()
    collector = attach_collector(page, dest)

    try:
        print(f"  Lade {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        await page.wait_for_timeout(5000)
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)
        return await save_fetched_page(page, collector, dest, url)
    finally:
        await page.close()


async def run(
    target: Optional[str],
    products_only: bool,
    limit: int,
    headed: bool,
    human: bool,
    attach: bool,
    cdp_url: Optional[str],
) -> int:
    cookies = load_pw_cookies()
    if not cookies:
        print("WARN: cookies.json fehlt")

    jobs: list[tuple[str, str]] = []
    if target:
        p = SITES / target
        status = p / "status.txt"
        url = ""
        if status.exists():
            for line in status.read_text(encoding="utf-8").splitlines():
                if line.startswith("url="):
                    url = line[4:].strip()
        if not url:
            print(f"FEHLER: Keine URL in {status}")
            return 1
        jobs.append((target, url))
    elif products_only and QUEUE.exists():
        data = json.loads(QUEUE.read_text(encoding="utf-8"))
        for item in data.get("products", []):
            jobs.append((f"produkte/{item['sku']}", item["url"]))
    else:
        jobs.append((
            "herren/ready-to-wear/vollstandige-ready-to-wear",
            "https://de.louisvuitton.com/deu-de/herren/ready-to-wear/"
            "vollstandige-ready-to-wear/_/N-tmfgzj3",
        ))

    if limit:
        jobs = jobs[:limit]

    ok = 0
    async with async_playwright() as p:
        if attach:
            browser, context, page = await connect_existing(p, cdp_url)
            warmed = True
            try:
                for i, (rel, url) in enumerate(jobs, 1):
                    print(f"\n[{i}/{len(jobs)}] {rel}")
                    success, warmed = await fetch_page_human(
                        page, url, rel, warmed, from_existing=True
                    )
                    if success:
                        ok += 1
                    await asyncio.sleep(2)
            finally:
                await browser.close()
        elif human:
            PROFILE_DIR.mkdir(exist_ok=True)
            ctx_opts: dict = {
                "headless": not headed,
                "locale": "de-DE",
                "viewport": {"width": 1440, "height": 900},
                "args": LAUNCH_ARGS,
            }
            if OPERA_BIN.is_file():
                ctx_opts["executable_path"] = str(OPERA_BIN)
            print("Opera GX mit Profil .opera-profile (wie beim manuellen Klon)")
            context: BrowserContext = await p.chromium.launch_persistent_context(
                str(PROFILE_DIR),
                **ctx_opts,
            )
            await context.add_init_script(STEALTH_JS)
            if cookies:
                await context.add_cookies(cookies)
            page = context.pages[0] if context.pages else await context.new_page()
            warmed = False
            for i, (rel, url) in enumerate(jobs, 1):
                print(f"\n[{i}/{len(jobs)}] {rel}")
                success, warmed = await fetch_page_human(page, url, rel, warmed)
                if success:
                    ok += 1
                await asyncio.sleep(3)
            await context.close()
        else:
            launch_opts: dict = {"headless": not headed, "args": LAUNCH_ARGS}
            if OPERA_BIN.is_file():
                launch_opts["executable_path"] = str(OPERA_BIN)
            browser = await p.chromium.launch(**launch_opts)
            context = await browser.new_context(
                locale="de-DE",
                viewport={"width": 1440, "height": 900},
            )
            if cookies:
                await context.add_cookies(cookies)
            await context.add_init_script(STEALTH_JS)
            for i, (rel, url) in enumerate(jobs, 1):
                print(f"\n[{i}/{len(jobs)}] {rel}")
                if await fetch_page_direct(context, url, rel):
                    ok += 1
                await asyncio.sleep(3)
            await context.close()
            await browser.close()

    print(f"\nFertig: {ok}/{len(jobs)}")
    return 0 if ok == len(jobs) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="LV Seiten + Assets (Scrapling-Stil)")
    parser.add_argument("--target", help="z.B. herren/ready-to-wear/vollstandige-ready-to-wear")
    parser.add_argument("--products-only", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--headed", action="store_true", default=True)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--human",
        action="store_true",
        default=True,
        help="Google → LV wie ein Mensch (Standard)",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="URL direkt öffnen ohne Google-Weg",
    )
    parser.add_argument(
        "--attach",
        action="store_true",
        help="Bestehenden Opera-Tab nutzen (CDP, kein neues Fenster)",
    )
    parser.add_argument(
        "--cdp",
        default="",
        help="CDP-URL, z.B. http://127.0.0.1:9222",
    )
    args = parser.parse_args()
    headed = not args.headless
    human = not args.direct
    cdp = args.cdp.strip() or None
    if args.attach and not cdp:
        found = discover_cdp_url()
        if found:
            print(f"CDP gefunden: {found}")
    return asyncio.run(
        run(
            args.target,
            args.products_only,
            args.limit,
            headed,
            human,
            args.attach,
            cdp,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
