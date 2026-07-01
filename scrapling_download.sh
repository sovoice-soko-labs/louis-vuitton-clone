#!/bin/bash
# Assets nachladen — Scrapling-Stil (Playwright + Response-Interceptor)
# Scrapling-Paket braucht Python 3.10+; dieses Script funktioniert mit Python 3.9.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PY=python3
if command -v python3.12 >/dev/null 2>&1; then PY=python3.12; fi
if command -v python3.11 >/dev/null 2>&1; then PY=python3.11; fi

echo "Python: $($PY --version)"
echo ""
echo "Voraussetzungen: ProtonVPN (DE) an, cookies.json vorhanden"
echo "Modus: Google → LV Homepage → Zielseite (menschenähnlich)"
echo ""

case "${1:-attach}" in
  attach|category)
    echo "=== Bestehender Opera-Tab (LV Homepage) → Kategorie ==="
    if $PY -c "from cdp_attach import discover_cdp_url; import sys; sys.exit(0 if discover_cdp_url() else 1)" 2>/dev/null; then
      $PY scrapling_fetch.py --attach --target herren/ready-to-wear/vollstandige-ready-to-wear
    else
      echo "CDP nicht aktiv — steuere offenen Opera-Tab per AppleScript (kein neues Fenster)"
      curl -sf "http://127.0.0.1:8765/health" >/dev/null 2>&1 || "$ROOT/start_listener.sh" &
      sleep 2
      $PY opera_navigate.py --mode category --wait 15
      echo ""
      echo "=== Assets aus gespeichertem HTML nachladen ==="
      $PY download_assets.py --target herren/ready-to-wear/vollstandige-ready-to-wear --delay 0.08
    fi
    ;;
  attach-test)
    echo "=== Test: 3 Produkte im offenen Tab ==="
    $PY scrapling_fetch.py --attach --products-only --limit 3
    ;;
  attach-products)
    echo "=== Alle Produktseiten im offenen Tab ==="
    read -r -p "Wirklich alle 183? (j/N) " ans
    [[ "${ans,,}" == "j" ]] || exit 0
    $PY scrapling_fetch.py --attach --products-only
    ;;
  category-new)
    echo "=== Kategorie (neues Opera-Fenster) ==="
    $PY scrapling_fetch.py --target herren/ready-to-wear/vollstandige-ready-to-wear --headed
    ;;
  products)
    echo "=== Alle Produktseiten (kann Stunden dauern) ==="
    read -r -p "Wirklich alle 183? (j/N) " ans
    [[ "${ans,,}" == "j" ]] || exit 0
    $PY scrapling_fetch.py --products-only --headed
    ;;
  test)
    echo "=== Test: 3 Produkte ==="
    $PY scrapling_fetch.py --products-only --limit 3 --headed
    ;;
  scrapling-pkg)
    echo "=== Echtes Scrapling (nur mit Python 3.10+) ==="
    ver=$($PY -c "import sys; print(sys.version_info >= (3,10))")
    if [ "$ver" != "True" ]; then
      echo "FEHLER: Scrapling braucht Python 3.10+"
      echo "Installiere von https://www.python.org/downloads/"
      exit 1
    fi
    $PY -m pip install "scrapling[fetchers]"
    $PY -m scrapling install
    echo "Scrapling installiert. Nutze: scrapling extract stealthy-fetch URL out.html"
    ;;
  *)
    echo "Nutzung: $0 [attach|category|attach-test|attach-products|category-new|products|test|scrapling-pkg]"
    echo ""
    echo "  attach / category   — offenen LV-Tab nutzen (Standard)"
    echo "  attach-test         — 3 Produkte"
    echo "  attach-products     — alle 183"
    echo "  category-new        — neues Opera-Fenster (alt)"
    exit 1
    ;;
esac
