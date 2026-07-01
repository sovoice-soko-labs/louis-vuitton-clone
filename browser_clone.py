#!/usr/bin/env python3
"""Clone Louis Vuitton pages with Playwright (persistent Chrome profile + interactive mode)."""

import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Union

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites"
PROFILE_DIR = ROOT / ".opera-profile"
COOKIES_FILE = ROOT / "cookies.json"

OPERA_GX_BIN = Path("/Applications/Opera GX.app/Contents/MacOS/Opera")
CHROME_BIN = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
BROWSER = os.environ.get("BROWSER", "opera-gx").lower()

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = window.chrome || { runtime: {} };
"""

HOMEPAGE = "https://de.louisvuitton.com/deu-de/homepage"

PAGES = [
    ("homepage", HOMEPAGE),
    (
        "herren/ready-to-wear",
        "https://de.louisvuitton.com/deu-de/herren/ready-to-wear",
    ),
    (
        "produkte/1AHVYE",
        "https://de.louisvuitton.com/deu-de/produkte/"
        "kurzarm-hemd-mit-monogram-motiv-auf-der-tasche-nvprod6310009v/1AHVYE",
    ),
    (
        "produkte/1AHVYO",
        "https://de.louisvuitton.com/deu-de/produkte/"
        "kurzarm-hemd-mit-monogram-motiv-auf-der-tasche-nvprod6320084v/1AHVYO",
    ),
    (
        "kategorie/t-shirts-und-poloshirts",
        "https://de.louisvuitton.com/deu-de/herren/ready-to-wear/"
        "t-shirts-und-poloshirts/_/N-to9uy2x",
    ),
    (
        "kategorie/t-shirts-und-poloshirts-xl",
        "https://de.louisvuitton.com/deu-de/herren/ready-to-wear/"
        "t-shirts-und-poloshirts/_/N-to9uy2xl",
    ),
]


def safe_name(url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    name = os.path.basename(urlparse(url).path) or "asset"
    name = re.sub(r"[^\w.\-]", "_", name)[:80]
    return f"{name}_{h}"


def is_blocked(text: str) -> bool:
    return "Access denied" in text or "Accès refusé" in text


def is_error_page(title: str, body: str) -> bool:
    return "Fehler aufgetreten" in title or "Fehler aufgetreten" in body[:800]


def is_valid_content(title: str, body: str, html: str) -> bool:
    if is_blocked(body) or is_error_page(title, body):
        return False
    if len(html) < 50_000:
        return False
    if len(body.strip()) < 200:
        return False
    return True


def load_cookies() -> List[dict]:
    if not COOKIES_FILE.exists():
        return []
    data = json.loads(COOKIES_FILE.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    raise ValueError("cookies.json muss ein JSON-Array sein")


def ensure_browsers() -> None:
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=False,
        capture_output=True,
    )


async def wait_for_enter(message: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: input(message))


def browser_executable() -> Optional[str]:
    if BROWSER in ("opera-gx", "operagx", "opera"):
        if OPERA_GX_BIN.is_file():
            return str(OPERA_GX_BIN)
    if BROWSER in ("chrome", "google-chrome"):
        if CHROME_BIN.is_file():
            return str(CHROME_BIN)
    if OPERA_GX_BIN.is_file():
        return str(OPERA_GX_BIN)
    if CHROME_BIN.is_file():
        return str(CHROME_BIN)
    return None


def browser_label() -> str:
    exe = browser_executable() or ""
    if "Opera" in exe:
        return "Opera GX"
    if "Chrome" in exe:
        return "Chrome"
    return "Chromium"


def launch_args() -> List[str]:
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
    ]


async def launch_browser(p, headless: bool, persistent: bool = False):
    exe = browser_executable()
    label = browser_label()
    launch_opts = {
        "headless": headless,
        "args": launch_args(),
    }
    context_opts = {**launch_opts, "locale": "de-DE"}
    if exe:
        launch_opts["executable_path"] = exe
        context_opts["executable_path"] = exe
        if persistent:
            PROFILE_DIR.mkdir(exist_ok=True)
            print(f"{label} starten (Profil: .opera-profile) …")
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                viewport=None,
                **context_opts,
            )
            await ctx.add_init_script(STEALTH_JS)
            return ctx
        print(f"{label} starten …")
        browser = await p.chromium.launch(**launch_opts)
        return browser

    ensure_browsers()
    print("Fallback Chromium …")
    if persistent:
        PROFILE_DIR.mkdir(exist_ok=True)
        return await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            viewport=None,
            headless=headless,
            locale="de-DE",
            args=launch_args(),
        )
    return await p.chromium.launch(headless=headless, args=launch_args())


async def open_cookies_browser(p, headless: bool = True) -> Browser:
    """Browser nur mit cookies.json — für Listener-gesteuerten Klon."""
    ensure_browsers()
    result = await launch_browser(p, headless=headless, persistent=False)
    if isinstance(result, Browser):
        return result
    browser = result.browser
    if browser is None:
        raise RuntimeError("Browser konnte nicht gestartet werden")
    return browser


async def open_context(p, interactive: bool) -> Union[BrowserContext, Browser]:
    """Persistentes Browser-Profil — Cookies bleiben zwischen Läufen erhalten."""
    try:
        return await launch_browser(p, headless=not interactive, persistent=True)
    except Exception as exc:
        print(f"    {browser_label()} nicht verfügbar ({exc}), Fallback …")
        ensure_browsers()
        browser = await p.chromium.launch(
            headless=not interactive,
            args=launch_args(),
        )
        return browser


async def get_page(context_or_browser) -> tuple:
    if isinstance(context_or_browser, BrowserContext):
        context = context_or_browser
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        return context, page, False

    context = await context_or_browser.new_context(locale="de-DE")
    cookies = load_cookies()
    if cookies:
        await context.add_cookies(cookies)
    page = await context.new_page()
    await page.add_init_script(STEALTH_JS)
    return context, page, True


async def download_asset(context, url: str, dest_dir: Path, subdir: str) -> Optional[str]:
    if not url or url.startswith("data:") or url.startswith("blob:"):
        return None
    try:
        resp = await context.request.get(url, timeout=30000)
        if not resp.ok:
            return None
        body = await resp.body()
        ext = Path(urlparse(url).path).suffix.split("?")[0] or ".bin"
        folder = dest_dir / subdir
        folder.mkdir(parents=True, exist_ok=True)
        fname = safe_name(url) + ext
        (folder / fname).write_bytes(body)
        return f"{subdir}/{fname}"
    except Exception:
        return None


async def navigate_with_warmup_refresh(page: Page, url: str) -> None:
    """Homepage zuerst, dann Ziel-URL, dann Refresh — wie manuell im Browser."""
    print("    1/3 Warmup: Homepage …")
    await page.goto(HOMEPAGE, wait_until="domcontentloaded", timeout=120000)
    await page.wait_for_timeout(4000)
    print("    2/3 Ziel-URL öffnen …")
    await page.goto(url, wait_until="domcontentloaded", timeout=120000)
    await page.wait_for_timeout(5000)
    print("    3/3 Refresh (F5) …")
    await page.reload(wait_until="domcontentloaded")
    await page.wait_for_timeout(6000)
    try:
        await page.wait_for_load_state("networkidle", timeout=45000)
    except Exception:
        pass


async def ensure_page_ready(page: Page, url: str, interactive: bool, use_refresh: bool = False) -> bool:
    try:
        if use_refresh:
            await navigate_with_warmup_refresh(page, url)
        else:
            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
            await page.wait_for_timeout(3000)
            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass
    except Exception as exc:
        print(f"    WARN navigation: {exc}")

    for attempt in range(15):
        title = await page.title()
        body = await page.inner_text("body")
        html = await page.content()
        if is_valid_content(title, body, html):
            await page.wait_for_timeout(2000)
            return True
        if is_error_page(title, body) or len(html) < 50_000:
            label = "Fehler/leer" if is_error_page(title, body) else "noch leer"
            print(f"    Seite {label} (Versuch {attempt + 1}/15) …")
            if not interactive and attempt % 2 == 1:
                await page.reload(wait_until="domcontentloaded")
                await page.wait_for_timeout(5000)
            elif not interactive:
                await page.wait_for_timeout(3000)
            continue
        if not interactive:
            await page.wait_for_timeout(2500)
            continue

        print("\n    Seite noch nicht bereit — im Browser-Fenster:")
        print("    1. Cookie-Banner akzeptieren falls nötig")
        print("    2. F5 / Refresh drücken")
        print("    3. Warten bis Produkte sichtbar sind")
        print("    4. Hier Enter drücken (q = abbrechen)\n")
        answer = await wait_for_enter("    Enter nach Refresh … ")
        if answer.strip().lower() == "q":
            return False
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)

    title = await page.title()
    body = await page.inner_text("body")
    html = await page.content()
    return is_valid_content(title, body, html)


async def save_page(context, page: Page, rel_path: str, url: str) -> bool:
    dest = SITES / rel_path
    dest.mkdir(parents=True, exist_ok=True)
    for sub in ("css", "js", "imgs"):
        (dest / sub).mkdir(exist_ok=True)

    title = await page.title()
    body_text = await page.inner_text("body")
    html = await page.content()
    blocked = not is_valid_content(title, body_text, html)

    if blocked:
        if len(html) < 50_000:
            print("    FEHLER: Seite leer/unvollständig — nicht gespeichert")
        elif is_error_page(title, body_text):
            print("    FEHLER: LV-Fehlerseite — nicht gespeichert")
        else:
            print("    BLOCKED: Seite nicht gespeichert")
        return False

    print(f"    OK: {title[:70]}")

    asset_map: Dict[str, str] = {}

    for link in await page.eval_on_selector_all(
        "link[rel='stylesheet']", "els => els.map(e => e.href)"
    ):
        local = await download_asset(context, link, dest, "css")
        if local:
            asset_map[link] = local

    for src in await page.eval_on_selector_all(
        "script[src]", "els => els.map(e => e.src)"
    ):
        local = await download_asset(context, src, dest, "js")
        if local:
            asset_map[src] = local

    for src in await page.eval_on_selector_all("img[src]", "els => els.map(e => e.src)"):
        local = await download_asset(context, src, dest, "imgs")
        if local:
            asset_map[src] = local

    for remote, local in sorted(asset_map.items(), key=lambda x: -len(x[0])):
        html = html.replace(remote, local)

    (dest / "index.html").write_text(html, encoding="utf-8")
    (dest / "status.txt").write_text(
        f"url={url}\ntitle={title}\nblocked={blocked}\n", encoding="utf-8"
    )
    return True


async def clone_page(
    context_or_browser,
    rel_path: str,
    url: str,
    interactive: bool,
    ephemeral_contexts: bool,
    use_refresh: bool = False,
) -> bool:
    print(f"\n=== {rel_path} ===\n    {url}")

    if ephemeral_contexts:
        context, page, _ = await get_page(context_or_browser)
    else:
        context = context_or_browser
        page = context.pages[0] if context.pages else await context.new_page()

    ready = await ensure_page_ready(page, url, interactive, use_refresh)
    if not ready:
        if ephemeral_contexts:
            await context.close()
        return False

    ok = await save_page(context, page, rel_path, url)
    if ephemeral_contexts:
        await context.close()
    return ok


def show_ip() -> None:
    try:
        with urllib.request.urlopen("https://ipinfo.io/json", timeout=8) as resp:
            info = json.loads(resp.read().decode())
        print(
            f"IP: {info.get('ip')} | {info.get('city')}, {info.get('country')} | "
            f"{info.get('org', '')[:50]}"
        )
    except Exception as exc:
        print(f"IP-Check fehlgeschlagen: {exc}")


async def clone_with_cookies(p, interactive: bool, headed: bool, pages: list, use_refresh: bool) -> int:
    cookies = load_cookies()
    if not cookies:
        print("FEHLER: cookies.json fehlt — Listener starten und LV in Opera GX besuchen.")
        return 1

    print(f"Cookie-Modus: {len(cookies)} Cookies aus cookies.json")
    show_ip()
    browser = await open_cookies_browser(p, headless=not headed)
    context = await browser.new_context(locale="de-DE")
    await context.add_cookies(cookies)
    await context.add_init_script(STEALTH_JS)
    page = await context.new_page()

    ok = 0
    for rel_path, url in pages:
        print(f"\n=== {rel_path} ===\n    {url}")
        ready = await ensure_page_ready(page, url, interactive, use_refresh)
        if ready and await save_page(context, page, rel_path, url):
            ok += 1

    await context.close()
    await browser.close()
    print(f"\n=== Fertig: {ok}/{len(pages)} Seiten erfolgreich ===")
    return 0 if ok == len(pages) else 1


async def main() -> int:
    parser = argparse.ArgumentParser(description="Louis Vuitton Seiten klonen")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Ohne manuelle Bestätigung",
    )
    parser.add_argument(
        "--cookies-only",
        action="store_true",
        help="Nur cookies.json verwenden (vom Listener)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Browser sichtbar (empfohlen mit VPN)",
    )
    parser.add_argument(
        "--only",
        metavar="PFAD",
        help="Nur eine Seite, z.B. kategorie/t-shirts-und-poloshirts-xl",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Homepage → URL → Refresh (wie manuell F5)",
    )
    args = parser.parse_args()
    interactive = not args.auto
    headed = args.headed or interactive
    use_refresh = args.refresh

    pages = PAGES
    if args.only:
        pages = [(p, u) for p, u in PAGES if p == args.only or args.only in p]
        if not pages:
            print(f"FEHLER: Unbekannter Pfad '{args.only}'")
            print("Verfügbar:", ", ".join(p for p, _ in PAGES))
            return 1

    show_ip()

    async with async_playwright() as p:
        if args.cookies_only:
            return await clone_with_cookies(p, interactive, headed, pages, use_refresh)

        if headed:
            print(f"{browser_label()} sichtbar — bei Block Enter drücken." if interactive else f"{browser_label()} sichtbar (Auto).")
        else:
            print("Auto-Modus (ohne Enter).")

        if COOKIES_FILE.exists():
            print(f"Zusätzlich: {len(load_cookies())} Cookies aus cookies.json")

        ok = 0
        ctx = await open_context(p, headed)
        ephemeral = isinstance(ctx, Browser)

        for rel_path, url in pages:
            if await clone_page(ctx, rel_path, url, interactive, ephemeral, use_refresh):
                ok += 1

        if isinstance(ctx, BrowserContext):
            await ctx.close()
        else:
            await ctx.close()

    print(f"\n=== Fertig: {ok}/{len(pages)} Seiten erfolgreich ===")
    if ok < len(pages) and interactive:
        print("Tipp: Beim nächsten Lauf sind Cookies im Profil .opera-profile gespeichert.")
    return 0 if ok == len(pages) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
