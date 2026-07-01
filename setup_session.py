#!/usr/bin/env python3
"""Einmalig Opera GX öffnen und Louis Vuitton manuell besuchen (Cookies werden gespeichert)."""

import asyncio
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
PROFILE_DIR = ROOT / ".opera-profile"
OPERA_GX_BIN = Path("/Applications/Opera GX.app/Contents/MacOS/Opera")
URL = "https://de.louisvuitton.com/deu-de/homepage"

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = window.chrome || { runtime: {} };
"""


async def main() -> None:
    PROFILE_DIR.mkdir(exist_ok=True)
    exe = str(OPERA_GX_BIN) if OPERA_GX_BIN.is_file() else None
    label = "Opera GX" if exe else "Chromium"
    print(f"{label} öffnet sich mit gespeichertem Profil (.opera-profile)")
    print("Bitte Louis Vuitton normal besuchen — Cookie-Banner akzeptieren.")
    print("Wenn die echte Homepage sichtbar ist: Terminal-Fenster schließen oder Ctrl+C.\n")

    launch_opts = {
        "user_data_dir": str(PROFILE_DIR),
        "headless": False,
        "locale": "de-DE",
        "viewport": None,
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    if exe:
        launch_opts["executable_path"] = exe

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(**launch_opts)
        await context.add_init_script(STEALTH_JS)
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(URL, wait_until="domcontentloaded")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nProfil gespeichert. Jetzt: ./clone.sh")
        finally:
            await context.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProfil gespeichert. Jetzt: ./clone.sh")
        sys.exit(0)
