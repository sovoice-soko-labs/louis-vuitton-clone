#!/usr/bin/env python3
"""Menschlicher Browser-Weg: Google → LV Homepage → Land/Sprache → Zielseite."""

import asyncio
import random
import re
from typing import Optional

from playwright.async_api import Page

HOMEPAGE = "https://de.louisvuitton.com/deu-de/homepage"

CONSENT_SELECTORS = (
    "#onetrust-accept-btn-handler",
    'button:has-text("Alle akzeptieren")',
    'button:has-text("Accept all")',
    'button:has-text("Zustimmen")',
    'button:has-text("Akzeptieren")',
)

LOCALE_SELECTORS = (
    'a[href*="/deu-de/"]',
    'button:has-text("Deutschland")',
    'a:has-text("Deutschland")',
    'button:has-text("Germany")',
    'a:has-text("Germany")',
    'button:has-text("Deutsch")',
)


async def human_pause(lo: int = 800, hi: int = 2200) -> None:
    await asyncio.sleep(random.uniform(lo / 1000, hi / 1000))


async def dismiss_overlays(page: Page) -> None:
    for sel in CONSENT_SELECTORS:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1200):
                await btn.click()
                await human_pause(400, 1000)
        except Exception:
            pass


async def ensure_german_locale(page: Page) -> None:
    if "de.louisvuitton.com" in page.url and "/deu-de/" in page.url:
        return
    for sel in LOCALE_SELECTORS:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=2000):
                await el.click()
                await human_pause(1500, 3500)
                await dismiss_overlays(page)
                if "/deu-de/" in page.url:
                    return
        except Exception:
            pass
    if "louisvuitton.com" in page.url and "/deu-de/" not in page.url:
        await page.goto(HOMEPAGE, wait_until="domcontentloaded", timeout=120_000)
        await human_pause(2000, 4000)
        await dismiss_overlays(page)


async def human_scroll(page: Page, deep: bool = False) -> None:
    steps = (350, 500, 700, 900, 1200, -300) if deep else (350, 500, -200, 700)
    for dy in steps:
        await page.mouse.wheel(0, dy)
        await human_pause(500, 1200)


async def wait_for_lv_content(page: Page, min_html: int = 50_000, attempts: int = 12) -> bool:
    """Warten bis Nuxt-Inhalt geladen (nicht nur Loader-Shell)."""
    for n in range(attempts):
        html = await page.content()
        title = await page.title()
        loader = await page.locator(".lv-page-loader").count()
        products = await page.locator(".lv-product-card, .lv-product-grid__item").count()
        if len(html) >= min_html and products > 5 and "Fehler aufgetreten" not in title:
            return True
        if len(html) >= min_html and "Designer-Kleidung" in title:
            return True
        if len(html) >= min_html and "/produkte/" in page.url:
            return True
        print(f"    Warte auf Inhalt ({n + 1}/{attempts}) · {len(html)//1024} KB · Produkte≈{products}")
        await dismiss_overlays(page)
        await human_scroll(page, deep=(n % 2 == 1))
        if n % 3 == 2:
            await page.reload(wait_until="domcontentloaded")
        await human_pause(2500, 5000)
    return False


async def human_nav_menu_rtw(page: Page) -> bool:
    """Herren → Ready-to-Wear → Vollständige Ready-to-Wear (wie im Browser)."""
    print("    Menü: Herren → Ready-to-Wear → Vollständige …")
    try:
        herren = page.get_by_role("link", name=re.compile(r"^Herren$", re.I)).first
        await herren.hover(timeout=8000)
        await human_pause(700, 1400)
        rtw = page.get_by_role("link", name=re.compile(r"Ready[- ]?to[- ]?Wear", re.I)).first
        await rtw.click(timeout=10000)
        await page.wait_for_load_state("domcontentloaded")
        await human_pause(2500, 4500)
        await dismiss_overlays(page)
        full = page.get_by_role("link", name=re.compile(r"Vollständige", re.I)).first
        if await full.count() > 0 and await full.is_visible(timeout=5000):
            await full.click(timeout=10000)
            await page.wait_for_load_state("domcontentloaded")
            await human_pause(2500, 4500)
            return True
        # Fallback: Link mit N-tmfgzj3
        cat = page.locator('a[href*="N-tmfgzj3"]').first
        if await cat.count() > 0:
            await cat.click(timeout=10000)
            await page.wait_for_load_state("domcontentloaded")
            await human_pause(2500, 4500)
            return True
    except Exception as exc:
        print(f"    Menü-Navigation fehlgeschlagen: {exc}")
    return False


async def human_google_to_lv(page: Page) -> None:
    """Wie ein Mensch: Google → Suche → LV-Klick → Cookies/Sprache."""
    print("    1/6 Google öffnen …")
    await page.goto("https://www.google.de/", wait_until="domcontentloaded", timeout=90_000)
    await human_pause(1500, 3000)
    await dismiss_overlays(page)

    print("    2/6 „louis vuitton“ eintippen …")
    box = page.locator('textarea[name="q"], input[name="q"]').first
    await box.click()
    await human_pause(300, 900)
    await box.press_sequentially("louis vuitton", delay=random.randint(65, 175))
    await human_pause(600, 1800)
    await box.press("Enter")
    await page.wait_for_load_state("domcontentloaded")
    await human_pause(2000, 4000)
    await dismiss_overlays(page)

    print("    3/6 LV-Suchergebnis anklicken …")
    link = page.locator(
        'a[href*="de.louisvuitton.com"], a[href*="louisvuitton.com/deu-de"]'
    ).first
    if await link.count() == 0:
        link = page.locator('a[href*="louisvuitton.com"]').filter(
            has_text=re.compile(r"Louis\s*Vuitton", re.I)
        ).first
    await link.click(timeout=45_000)
    await page.wait_for_load_state("domcontentloaded")
    await human_pause(2500, 5000)
    await dismiss_overlays(page)

    print("    4/6 Land & Sprache (Deutschland) …")
    await ensure_german_locale(page)

    print("    5/6 Menü: Herren …")
    try:
        herren = page.get_by_role("link", name=re.compile(r"^Herren$", re.I)).first
        if await herren.is_visible(timeout=4000):
            await herren.hover()
            await human_pause(600, 1200)
    except Exception:
        pass

    print("    6/6 Homepage kurz ansehen …")
    if "/deu-de/" not in page.url:
        await page.goto(HOMEPAGE, wait_until="domcontentloaded", timeout=120_000)
        await human_pause(2000, 4000)
        await dismiss_overlays(page)
    await human_scroll(page)


async def human_go_to_target(page: Page, url: str) -> None:
    """Nach Warmup zur Zielseite — per Menü oder URL, scrollen, warten."""
    use_menu = "vollstandige-ready-to-wear" in url and "N-tmfgzj3" in url
    if use_menu:
        if not await human_nav_menu_rtw(page):
            print(f"    Fallback: direkte URL …")
            await page.goto(url, wait_until="domcontentloaded", timeout=120_000)
    else:
        print(f"    Ziel: {url[:70]}…")
        await human_pause(1000, 2500)
        await page.goto(url, wait_until="domcontentloaded", timeout=120_000)

    await human_pause(3000, 6000)
    try:
        await page.wait_for_load_state("networkidle", timeout=45_000)
    except Exception:
        pass
    await dismiss_overlays(page)
    await human_scroll(page, deep=True)
    print("    Refresh (F5) …")
    await page.reload(wait_until="domcontentloaded")
    await human_pause(3000, 6000)
    await dismiss_overlays(page)
    await human_scroll(page, deep=True)
    await wait_for_lv_content(page)
