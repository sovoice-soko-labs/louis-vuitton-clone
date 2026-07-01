#!/usr/bin/env python3
"""Räumt Opera GX auf: gxcorner-Fenster + fertige LV-Produkt-Tabs schließen."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites" / "produkte"
QUEUE = ROOT / "products_queue.json"
MIN_BYTES = 50_000


def saved_skus() -> set[str]:
    skus: set[str] = set()
    if QUEUE.is_file():
        data = json.loads(QUEUE.read_text(encoding="utf-8"))
        for p in data.get("products", []):
            if p.get("saved"):
                skus.add(p["sku"])
    if SITES.is_dir():
        for d in SITES.iterdir():
            html = d / "index.html"
            if d.is_dir() and html.is_file() and html.stat().st_size >= MIN_BYTES:
                skus.add(d.name)
    return skus


def run_applescript(script: str, timeout: int = 180) -> str:
    return subprocess.check_output(
        ["osascript", "-e", script], text=True, timeout=timeout
    ).strip()


def stats() -> tuple[int, int, int, int]:
    script = '''
tell application "Opera GX"
  set winCount to count of windows
  set tabCount to 0
  set gxCount to 0
  set lvCount to 0
  repeat with w in windows
    try
      set n to count of tabs of w
      set tabCount to tabCount + n
      repeat with i from 1 to n
        try
          set u to URL of tab i of w
          if u contains "gxcorner.games" then set gxCount to gxCount + 1
          if u contains "louisvuitton.com" then set lvCount to lvCount + 1
        end try
      end repeat
    end try
  end repeat
  return (winCount as text) & "," & (tabCount as text) & "," & (gxCount as text) & "," & (lvCount as text)
end tell
'''
    try:
        parts = run_applescript(script, 90).split(",")
        return tuple(int(x) for x in parts)
    except Exception:
        return -1, -1, -1, -1


def close_gxcorner_windows() -> int:
    script = '''
tell application "Opera GX"
  set closedWins to 0
  set closedTabs to 0
  repeat with w in windows
    try
      set n to count of tabs of w
      if n is 1 then
        set u to URL of tab 1 of w
        if u contains "gxcorner.games" or u is "about:blank" then
          close w
          set closedWins to closedWins + 1
        end if
      else
        repeat with i from n to 1 by -1
          try
            set u to URL of tab i of w
            if u contains "gxcorner.games" or u is "about:blank" then
              close tab i of w
              set closedTabs to closedTabs + 1
            end if
          end try
        end repeat
      end if
    end try
  end repeat
  return (closedWins as text) & "," & (closedTabs as text)
end tell
'''
    try:
        wins, tabs = run_applescript(script).split(",")
        return int(wins) + int(tabs)
    except Exception as exc:
        print(f"gxcorner: {exc}")
        return 0


def close_saved_product_tabs(skus: set[str], chunk_size: int = 15) -> int:
    if not skus:
        return 0
    total = 0
    sku_list = sorted(skus)
    for start in range(0, len(sku_list), chunk_size):
        chunk = sku_list[start : start + chunk_size]
        conditions = " or ".join(f'u contains "{s}"' for s in chunk)
        script = f'''
tell application "Opera GX"
  set closedCount to 0
  repeat with w in windows
    try
      set n to count of tabs of w
      repeat with i from n to 1 by -1
        try
          set u to URL of tab i of w
          if u contains "louisvuitton.com" and u contains "/deu-de/produkte/" then
            if {conditions} then
              close tab i of w
              set closedCount to closedCount + 1
            end if
          end if
        end try
      end repeat
    end try
  end repeat
  return closedCount
end tell
'''
        try:
            n = int(run_applescript(script))
            if n:
                print(f"  gespeicherte Produkte: {n} (Batch {start // chunk_size + 1})")
            total += n
        except Exception as exc:
            print(f"produkte batch: {exc}")
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gx-only", action="store_true", help="Nur gxcorner-Fenster schließen")
    args = parser.parse_args()

    before = stats()
    if before[0] >= 0:
        print(f"Vorher: {before[0]} Fenster, {before[1]} Tabs "
              f"(gxcorner: {before[2]}, LV: {before[3]})")

    total = 0
    for i in range(12):
        n = close_gxcorner_windows()
        total += n
        if n:
            print(f"  gxcorner Durchlauf {i + 1}: {n}")
        if n == 0:
            break

    if not args.gx_only:
        skus = saved_skus()
        for i in range(8):
            n = close_saved_product_tabs(skus)
            total += n
            if n:
                print(f"  gespeicherte Produkte Durchlauf {i + 1}: {n}")
            if n == 0:
                break

    after = stats()
    if after[0] >= 0:
        print(f"Nachher: {after[0]} Fenster, {after[1]} Tabs "
              f"(gxcorner: {after[2]}, LV: {after[3]})")
    print(f"Aufgeräumt: {total} Fenster/Tabs geschlossen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
