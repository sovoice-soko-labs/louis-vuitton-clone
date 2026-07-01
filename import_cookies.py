#!/usr/bin/env python3
"""
Cookies manuell importieren → cookies.json

Unterstützte Formate:
  - Cookie-Editor / Chrome Extension JSON
  - Playwright cookies.json
  - Netscape cookies.txt
  - Einfache Cookie-Zeile: name=wert; name2=wert2
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "cookies.json"
DEFAULT_IN = ROOT / "cookies_raw.json"

SAME_SITE = {
    "no_restriction": "None",
    "lax": "Lax",
    "strict": "Strict",
    "unspecified": "Lax",
}


def to_playwright(cookies: List[dict]) -> List[dict]:
    out: List[dict] = []
    for c in cookies:
        if "name" not in c or "value" not in c:
            continue
        item: Dict[str, Any] = {
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain") or ".louisvuitton.com",
            "path": c.get("path", "/"),
        }
        exp = c.get("expires") or c.get("expirationDate")
        if exp:
            item["expires"] = int(exp)
        if "httpOnly" in c:
            item["httpOnly"] = bool(c["httpOnly"])
        if "secure" in c:
            item["secure"] = bool(c["secure"])
        ss = c.get("sameSite")
        if isinstance(ss, str):
            item["sameSite"] = SAME_SITE.get(ss.lower(), ss) if ss in SAME_SITE else (
                ss if ss in ("Lax", "Strict", "None") else "Lax"
            )
        out.append(item)
    return out


def parse_json(data: Any) -> List[dict]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "cookies" in data:
        return data["cookies"]
    raise ValueError("JSON muss ein Array von Cookies sein")


def parse_netscape(text: str) -> List[dict]:
    cookies: List[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, _flag, path, secure, expiry, name, value = parts[:7]
        item: Dict[str, Any] = {
            "domain": domain,
            "path": path,
            "name": name,
            "value": value,
            "secure": secure.upper() == "TRUE",
            "httpOnly": False,
        }
        if expiry and expiry != "0":
            item["expirationDate"] = int(expiry)
        cookies.append(item)
    return cookies


def parse_header_string(text: str) -> List[dict]:
    cookies: List[dict] = []
    for part in text.replace("\n", ";").split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies.append(
            {
                "name": name.strip(),
                "value": value.strip(),
                "domain": ".louisvuitton.com",
                "path": "/",
            }
        )
    return cookies


def detect_and_parse(text: str) -> List[dict]:
    text = text.strip()
    if not text:
        raise ValueError("Datei ist leer")

    if text.startswith("{") or text.startswith("["):
        return parse_json(json.loads(text))

    if "\t" in text and "louisvuitton" in text.lower():
        return parse_netscape(text)

    if "=" in text:
        return parse_header_string(text)

    raise ValueError("Unbekanntes Format")


def filter_lv(cookies: List[dict]) -> List[dict]:
    lv = []
    for c in cookies:
        domain = (c.get("domain") or "").lower()
        if "louisvuitton" in domain or not domain:
            lv.append(c)
    return lv if lv else cookies


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cookies manuell importieren",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ANLEITUNG (Chrome):

  Variante A — Cookie-Editor Extension (empfohlen):
    1. Chrome Web Store: "Cookie-Editor" installieren
    2. de.louisvuitton.com besuchen (echte Seite, kein Access denied)
    3. Cookie-Editor öffnen → Export → JSON kopieren
    4. In cookies_raw.json speichern
    5. python3 import_cookies.py
    6. ./clone.sh

  Variante B — DevTools (nur sichtbare Cookies, oft nicht ausreichend):
    1. F12 → Application → Cookies → https://de.louisvuitton.com
    2. Rechtsklick auf Cookie-Zeilen → manuell in JSON eintragen
       oder Cookie-Editor nutzen (httpOnly-Cookies gehen so nicht!)

  Variante C — Header-Zeile (einfach, aber unvollständig):
    Datei mit Inhalt:  name1=wert1; name2=wert2
""",
    )
    parser.add_argument("file", nargs="?", help="Import-Datei (Standard: cookies_raw.json)")
    parser.add_argument("--all-domains", action="store_true", help="Nicht nur louisvuitton.com filtern")
    args = parser.parse_args()

    src = Path(args.file) if args.file else DEFAULT_IN
    if not src.exists():
        print(f"FEHLER: {src} nicht gefunden.\n")
        print("Erstelle die Datei und füge deinen Cookie-Export ein.")
        print("Dann: python3 import_cookies.py")
        print("\nHilfe: python3 import_cookies.py --help")
        DEFAULT_IN.write_text("[]\n", encoding="utf-8")
        print(f"\nLeere Vorlage erstellt: {DEFAULT_IN}")
        return 1

    text = src.read_text(encoding="utf-8")
    try:
        raw = detect_and_parse(text)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"FEHLER beim Lesen von {src}: {exc}")
        return 1

    if not args.all_domains:
        raw = filter_lv(raw)

    pw = to_playwright(raw)
    if not pw:
        print("FEHLER: Keine gültigen Cookies gefunden.")
        return 1

    OUT.write_text(json.dumps(pw, indent=2), encoding="utf-8")
    print(f"✓ {len(pw)} Cookies → {OUT}")
    print("Jetzt klonen: ./clone.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
