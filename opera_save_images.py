#!/usr/bin/env python3
"""
Produkt-Bilder: offener Opera-Tab → Produkt öffnen → Bilder in sites/produkte/<SKU>/imgs/

Wie „Rechtsklick → Bild speichern“, aber automatisch:
  1. AppleScript: URL im bestehenden Opera-Tab öffnen (kein neues Fenster)
  2. Warten bis Seite + Extension HTML gespeichert haben
  3. Headless Browser lädt sichtbare Produktbilder in den Produktordner
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / "products_queue.json"
SITES = ROOT / "sites"
MIN_IMGS = 15


def run_applescript(script: str) -> str:
    return subprocess.check_output(["osascript", "-e", script], text=True, timeout=90).strip()


def find_lv_tab() -> Optional[Tuple[int, int, str]]:
    from opera_navigate import find_lv_tab as _find

    return _find()


def use_front_tab() -> Tuple[int, int, str]:
    """Aktiven Tab im vordersten Fenster — wie du gerade arbeitest."""
    script = '''
tell application "Opera GX"
  activate
  tell front window
    set wi to index
    set ti to active tab index
    set u to URL of active tab
    return (wi as text) & "|||" & (ti as text) & "|||" & u
  end tell
end tell
'''
    out = run_applescript(script)
    w, t, u = out.split("|||", 2)
    return int(w), int(t), u


def set_tab_url(window_i: int, tab_i: int, url: str) -> None:
    from opera_navigate import set_tab_url as _set

    _set(window_i, tab_i, url)


def img_count(sku: str) -> int:
    d = SITES / "produkte" / sku / "imgs"
    if not d.is_dir():
        return 0
    return sum(1 for f in d.iterdir() if f.is_file() and f.stat().st_size > 500)


def download_for_sku(sku: str, headless: bool) -> int:
    cmd = [
        sys.executable,
        str(ROOT / "browser_download_assets.py"),
        "--target",
        f"produkte/{sku}",
    ]
    if headless:
        cmd.append("--headless")
    r = subprocess.run(cmd, cwd=str(ROOT))
    return r.returncode


def listener_ok() -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Bilder via offenem Opera-Tab")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--min-imgs", type=int, default=MIN_IMGS)
    parser.add_argument("--wait", type=int, default=12, help="Sek. nach Navigation")
    parser.add_argument("--front-tab", action="store_true", default=True, help="Aktiven Tab nutzen")
    parser.add_argument("--headed-dl", action="store_true", default=True, help="Download mit sichtbarem Browser")
    parser.add_argument("--headless-dl", action="store_true", help="Download headless (oft blockiert)")
    args = parser.parse_args()

    if not listener_ok():
        print("Starte Listener für HTML-Save …")
        subprocess.Popen(
            [str(ROOT / "start_listener.sh")],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)

    if args.front_tab:
        wi, ti, cur = use_front_tab()
        if "louisvuitton.com" not in cur:
            found = find_lv_tab()
            if found:
                wi, ti, cur = found
                print(f"Front-Tab ist kein LV — nutze LV-Tab [{wi}/{ti}]")
            else:
                print(f"WARN: Aktiver Tab ist nicht LV: {cur[:70]}")
        print(f"Opera-Tab [{wi}/{ti}]: {cur[:80]}")
    else:
        found = find_lv_tab()
        if not found:
            print("FEHLER: Kein LV-Tab. Bitte louisvuitton.com in Opera öffnen.")
            return 1
        wi, ti, cur = found
        print(f"LV-Tab [{wi}/{ti}]: {cur[:80]}")

    products = json.loads(QUEUE.read_text(encoding="utf-8")).get("products", [])
    if args.limit:
        products = products[: args.limit]

    ok = 0
    for i, p in enumerate(products, 1):
        sku = p["sku"]
        url = p["url"]
        n = img_count(sku)
        if args.skip_existing and n >= args.min_imgs:
            print(f"[{i}/{len(products)}] {sku} — übersprungen ({n} Bilder)")
            ok += 1
            continue

        print(f"\n[{i}/{len(products)}] {sku} — öffne im Opera-Tab …")
        set_tab_url(wi, ti, url)
        time.sleep(args.wait)

        print(f"  Lade Bilder → sites/produkte/{sku}/imgs/")
        if download_for_sku(sku, headless=args.headless_dl) == 0:
            n2 = img_count(sku)
            print(f"  OK: {n2} Bilder")
            if n2 >= args.min_imgs:
                ok += 1
        else:
            print(f"  WARN: Download unvollständig ({img_count(sku)} Bilder)")

        time.sleep(1)

    print(f"\nFertig: {ok}/{len(products)} mit genug Bildern")
    return 0 if ok == len(products) else 1


if __name__ == "__main__":
    raise SystemExit(main())
