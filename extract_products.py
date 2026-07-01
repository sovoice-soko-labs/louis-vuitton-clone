#!/usr/bin/env python3
"""Produkt-URLs aus gespeicherter Kategorie-Seite extrahieren."""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites"
DEFAULT_SOURCE = SITES / "herren/ready-to-wear/vollstandige-ready-to-wear/index.html"
QUEUE_FILE = ROOT / "products_queue.json"
MIN_BYTES = 50_000

SKU_RE = re.compile(r"^[A-Z0-9]{5,8}$")
URL_RE = re.compile(
    r"(?:https://de\.louisvuitton\.com)?(/deu-de/produkte/[^\"'\s<>]+)",
    re.I,
)


def normalize_url(path: str) -> str:
    path = path.split("?")[0].split("#")[0].rstrip("/")
    return f"https://de.louisvuitton.com{path}"


def extract_from_html(html: str) -> list[dict]:
    seen: dict[str, dict] = {}
    for match in URL_RE.finditer(html):
        url = normalize_url(match.group(1))
        sku = url.rsplit("/", 1)[-1]
        if not SKU_RE.match(sku):
            continue
        seen[sku] = {"sku": sku, "url": url}
    return sorted(seen.values(), key=lambda x: x["sku"])


def product_saved(sku: str) -> bool:
    html = SITES / "produkte" / sku / "index.html"
    return html.is_file() and html.stat().st_size >= MIN_BYTES


def build_queue(products: list[dict]) -> dict:
    items = []
    for p in products:
        items.append({**p, "saved": product_saved(p["sku"])})
    saved = sum(1 for i in items if i["saved"])
    return {
        "total": len(items),
        "saved": saved,
        "pending": len(items) - saved,
        "products": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Produkt-URLs aus Kategorie-HTML extrahieren")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Gespeicherte Kategorie index.html",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Nur Fortschritt anzeigen (Queue muss existieren)",
    )
    args = parser.parse_args()

    if args.status and QUEUE_FILE.exists():
        data = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        data = build_queue(data.get("products", []))
        QUEUE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Gespeichert: {data['saved']}/{data['total']} · Offen: {data['pending']}")
        return 0

    if not args.source.is_file():
        print(f"FEHLER: {args.source} fehlt")
        return 1

    html = args.source.read_text(encoding="utf-8", errors="ignore")
    products = extract_from_html(html)
    data = build_queue(products)
    QUEUE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Gefunden: {data['total']} Produkte")
    print(f"Bereits gespeichert: {data['saved']}")
    print(f"Noch offen: {data['pending']}")
    print(f"Queue: {QUEUE_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
