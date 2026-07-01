#!/usr/bin/env python3
"""An bestehenden Browser per CDP anbinden (kein neues Fenster)."""

import os
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import urllib.error
import urllib.request

from playwright.async_api import Browser, BrowserContext, Page, Playwright

DEFAULT_CDP_PORTS = (9222, 9223, 9333)
CDP_URL = os.environ.get("CDP_URL", "")


def probe_cdp_url(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/json/version", timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def discover_cdp_url() -> Optional[str]:
    if CDP_URL and probe_cdp_url(CDP_URL):
        return CDP_URL.rstrip("/")
    for port in DEFAULT_CDP_PORTS:
        url = f"http://127.0.0.1:{port}"
        if probe_cdp_url(url):
            return url
    return None


def _lv_score(url: str) -> int:
    u = url.lower()
    if "louisvuitton.com" not in u:
        return -1
    score = 10
    if "homepage" in u:
        score += 100
    if "/deu-de/" in u:
        score += 50
    if "de.louisvuitton.com" in u:
        score += 20
    if re.search(r"/deu-de/?$", urlparse(u).path):
        score += 80
    return score


def list_lv_pages(browser: Browser) -> List[Page]:
    pages: List[Page] = []
    for ctx in browser.contexts:
        for page in ctx.pages:
            if "louisvuitton.com" in page.url:
                pages.append(page)
    return pages


async def connect_existing(
    p: Playwright, cdp_url: Optional[str] = None
) -> Tuple[Browser, BrowserContext, Page]:
    url = cdp_url or discover_cdp_url()
    if not url:
        raise RuntimeError(
            "Kein Debug-Port gefunden (9222).\n"
            "Opera GX einmal schließen und starten mit:\n"
            '  ./start_opera_debug.sh\n'
            "Dann LV-Homepage öffnen und erneut versuchen."
        )

    print(f"Verbinde mit bestehendem Browser: {url}")
    browser = await p.chromium.connect_over_cdp(url)

    lv_pages = list_lv_pages(browser)
    if not lv_pages:
        raise RuntimeError(
            "Browser verbunden, aber kein Louis-Vuitton-Tab gefunden.\n"
            "Bitte de.louisvuitton.com/deu-de/homepage im offenen Opera lassen."
        )

    page = max(lv_pages, key=lambda pg: _lv_score(pg.url))
    context = page.context
    print(f"Nutze Tab: {page.url[:90]}")
    return browser, context, page
