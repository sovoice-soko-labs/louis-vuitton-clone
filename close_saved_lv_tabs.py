#!/usr/bin/env python3
"""Schließt Opera-GX-Tabs für bereits gespeicherte LV-Produkte (mehrere Durchläufe)."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites" / "produkte"
QUEUE = ROOT / "products_queue.json"
MIN_BYTES = 50_000


def saved_skus(keep_sku: str = "") -> set[str]:
    skus: set[str] = set()
    if QUEUE.is_file():
        data = json.loads(QUEUE.read_text(encoding="utf-8"))
        for p in data.get("products", []):
            if p.get("saved"):
                skus.add(p["sku"])
    if SITES.is_dir():
        for d in SITES.iterdir():
            if not d.is_dir():
                continue
            html = d / "index.html"
            if html.is_file() and html.stat().st_size >= MIN_BYTES:
                skus.add(d.name)
    if keep_sku:
        skus.discard(keep_sku)
    return skus


def applescript_close_pass(skus: set[str], keep_active: bool) -> int:
    if not skus:
        return 0

    sku_literals = ", ".join(f'"{s}"' for s in sorted(skus))
    keep_clause = """
        if keepActive then
          try
            if t is active tab of front window then set shouldClose to false
          end try
        end if
    """ if keep_active else ""

    script = f'''
on shouldCloseUrl(u, savedSkus)
  if u does not contain "louisvuitton.com" then return false
  if u does not contain "/deu-de/produkte/" then return false
  repeat with sku in savedSkus
    if u contains (sku as text) then return true
  end repeat
  return false
end shouldCloseUrl

tell application "Opera GX"
  set savedSkus to {{{sku_literals}}}
  set closedCount to 0
  set keepActive to {"true" if keep_active else "false"}
  repeat with w in windows
    try
      set n to count of tabs of w
      repeat with i from n to 1 by -1
        try
          set t to tab i of w
          set u to URL of t
          set shouldClose to shouldCloseUrl(u, savedSkus)
          {keep_clause.strip()}
          if shouldClose then
            close t
            set closedCount to closedCount + 1
          end if
        end try
      end repeat
    end try
  end repeat
  return closedCount
end tell
'''
    try:
        out = subprocess.check_output(["osascript", "-e", script], text=True, timeout=120).strip()
        return int(out or 0)
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Warnung: Durchlauf fehlgeschlagen ({exc})")
        return 0


def close_tabs(skus: set[str], keep_active: bool, max_passes: int = 15) -> int:
    total = 0
    for i in range(max_passes):
        n = applescript_close_pass(skus, keep_active)
        total += n
        if n == 0:
            break
        print(f"  Durchlauf {i + 1}: {n} Tabs geschlossen")
    return total


def count_lv_tabs() -> tuple[int, int]:
    script = '''
tell application "Opera GX"
  set lvCount to 0
  set prodCount to 0
  repeat with w in windows
    try
      set n to count of tabs of w
      repeat with i from 1 to n
        try
          set u to URL of tab i of w
          if u contains "louisvuitton.com" then
            set lvCount to lvCount + 1
            if u contains "/deu-de/produkte/" then set prodCount to prodCount + 1
          end if
        end try
      end repeat
    end try
  end repeat
  return (lvCount as text) & "," & (prodCount as text)
end tell
'''
    try:
        out = subprocess.check_output(["osascript", "-e", script], text=True, timeout=60).strip()
        lv, prod = out.split(",", 1)
        return int(lv), int(prod)
    except Exception:
        return -1, -1


def main() -> int:
    parser = argparse.ArgumentParser(description="Fertige LV-Produkt-Tabs in Opera GX schließen")
    parser.add_argument("keep_sku", nargs="?", default="", help="Dieses SKU-Tab offen lassen")
    parser.add_argument("--no-keep-active", action="store_true", help="Auch aktiven Tab schließen")
    args = parser.parse_args()

    skus = saved_skus(args.keep_sku)
    before_lv, before_prod = count_lv_tabs()
    if before_lv >= 0:
        print(f"Vorher: {before_lv} LV-Tabs ({before_prod} Produkt-Tabs)")

    total = close_tabs(skus, keep_active=not args.no_keep_active)

    after_lv, after_prod = count_lv_tabs()
    if after_lv >= 0:
        print(f"Nachher: {after_lv} LV-Tabs ({after_prod} Produkt-Tabs)")

    print(f"Gesamt geschlossen: {total} · Gespeicherte SKUs: {len(skus)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
