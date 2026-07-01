#!/usr/bin/env python3
"""Navigation im bereits offenen Opera-GX-Tab (kein neues Fenster, kein CDP)."""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

ROOT = Path(__file__).resolve().parent

CATEGORY_URL = (
    "https://de.louisvuitton.com/deu-de/herren/ready-to-wear/"
    "vollstandige-ready-to-wear/_/N-tmfgzj3"
)
RTW_URL = "https://de.louisvuitton.com/deu-de/herren/ready-to-wear"
HOMEPAGE = "https://de.louisvuitton.com/deu-de/homepage"


def run_applescript(script: str, timeout: int = 60) -> str:
    return subprocess.check_output(
        ["osascript", "-e", script], text=True, timeout=timeout
    ).strip()


def find_lv_tab() -> Optional[Tuple[int, int, str]]:
    """(window_index, tab_index, url) — 1-basiert für AppleScript."""
    script = '''
tell application "Opera GX"
  set bestScore to -1
  set bestW to 0
  set bestT to 0
  set bestU to ""
  repeat with wi from 1 to count of windows
    set w to window wi
    try
      set n to count of tabs of w
      repeat with ti from 1 to n
        try
          set u to URL of tab ti of w
          if u contains "louisvuitton.com" then
            set sc to 10
            if u contains "homepage" then set sc to sc + 100
            if u contains "/deu-de/" then set sc to sc + 50
            if u contains "de.louisvuitton.com" then set sc to sc + 20
            if sc > bestScore then
              set bestScore to sc
              set bestW to wi
              set bestT to ti
              set bestU to u
            end if
          end if
        end try
      end repeat
    end try
  end repeat
  if bestScore < 0 then return ""
  return (bestW as text) & "|||" & (bestT as text) & "|||" & bestU
end tell
'''
    try:
        out = run_applescript(script)
        if not out:
            return None
        parts = out.split("|||", 2)
        if len(parts) != 3:
            return None
        return int(parts[0]), int(parts[1]), parts[2]
    except Exception:
        return None


def activate_tab(window_i: int, tab_i: int) -> None:
    script = f'''
tell application "Opera GX"
  activate
  set w to window {window_i}
  set index of w to 1
  set active tab index of w to {tab_i}
end tell
'''
    run_applescript(script)


def set_tab_url(window_i: int, tab_i: int, url: str) -> None:
    safe = url.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "Opera GX"
  activate
  set t to tab {tab_i} of window {window_i}
  set URL of t to "{safe}"
  set active tab index of window {window_i} to {tab_i}
end tell
'''
    run_applescript(script)


def navigate_category_human(window_i: int, tab_i: int) -> None:
    """Home → Herren RTW → Kategorie (gleicher Tab, mit Pausen)."""
    steps = [
        ("Homepage", HOMEPAGE),
        ("Herren Ready-to-Wear", RTW_URL),
        ("Vollständige Ready-to-Wear", CATEGORY_URL),
    ]
    for label, url in steps:
        print(f"  → {label}")
        set_tab_url(window_i, tab_i, url)
        time.sleep(6)


def main() -> int:
    parser = argparse.ArgumentParser(description="LV-Navigation im offenen Opera-Tab")
    parser.add_argument(
        "--mode",
        choices=("category", "url"),
        default="category",
    )
    parser.add_argument("--url", default=CATEGORY_URL)
    parser.add_argument("--wait", type=int, default=12, help="Sekunden nach Navigation")
    args = parser.parse_args()

    found = find_lv_tab()
    if not found:
        print("FEHLER: Kein Louis-Vuitton-Tab in Opera GX gefunden.")
        print("Bitte de.louisvuitton.com/deu-de/homepage offen lassen.")
        return 1

    wi, ti, current = found
    print(f"Nutze Tab [{wi}/{ti}]: {current[:85]}")

    activate_tab(wi, ti)
    time.sleep(1)

    if args.mode == "category":
        navigate_category_human(wi, ti)
    else:
        set_tab_url(wi, ti, args.url)
        time.sleep(args.wait)

    print(f"Fertig — Tab navigiert. Warte {args.wait}s auf Extension-Save …")
    time.sleep(args.wait)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
