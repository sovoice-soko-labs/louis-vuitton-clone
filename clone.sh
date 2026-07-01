#!/bin/bash
# Louis Vuitton Website-Klon
# Empfohlener Workflow: ./start_listener.sh → Extension in Opera GX → LV besuchen

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SITES="$ROOT/sites"
MODE="${1:-}"

ensure_playwright() {
  if ! python3 -c "import playwright" 2>/dev/null; then
    echo "=== Playwright installieren ==="
    pip3 install --user playwright
  fi
  python3 -m playwright install chromium 2>/dev/null || true
}

run_cookie_clone() {
  ensure_playwright
  python3 "$ROOT/browser_clone.py" --cookies-only --auto
}

run_interactive_clone() {
  ensure_playwright
  python3 "$ROOT/browser_clone.py"
}

run_goclone_assets() {
  local UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  clone_one() {
    local url="$1" dest="$2"
    echo "=== goclone: $url ==="
    rm -rf "$ROOT/de.louisvuitton.com"
    "$ROOT/goclone" "$url" -u "$UA" || true
    mkdir -p "$dest"
    [ -d "$ROOT/de.louisvuitton.com" ] && cp -R "$ROOT/de.louisvuitton.com/." "$dest/" && rm -rf "$ROOT/de.louisvuitton.com"
  }
  mkdir -p "$SITES"
  clone_one "https://de.louisvuitton.com/deu-de/homepage" "$SITES/homepage"
  clone_one "https://de.louisvuitton.com/deu-de/produkte/kurzarm-hemd-mit-monogram-motiv-auf-der-tasche-nvprod6310009v/1AHVYE" "$SITES/produkte/1AHVYE"
  clone_one "https://de.louisvuitton.com/deu-de/produkte/kurzarm-hemd-mit-monogram-motiv-auf-der-tasche-nvprod6320084v/1AHVYO" "$SITES/produkte/1AHVYO"
  clone_one "https://de.louisvuitton.com/deu-de/herren/ready-to-wear/t-shirts-und-poloshirts/_/N-to9uy2x" "$SITES/kategorie/t-shirts-und-poloshirts"
  clone_one "https://de.louisvuitton.com/deu-de/herren/ready-to-wear/t-shirts-und-poloshirts/_/N-to9uy2xl" "$SITES/kategorie/t-shirts-und-poloshirts-xl"
}

show_help() {
  cat <<EOF
Louis Vuitton Klon — Befehle

  ./clone_with_vpn.sh       Klon mit Proton VPN (empfohlen für echte Seiten)
  ./reclone_xl.sh           XL-Kategorie über VPN neu klonen
  ./start_local.sh          Alle Seiten lokal (http://localhost:5000)
  ./start_listener.sh       Listener + Extension (echte de.louisvuitton.com Seiten)
  ./import_cookies.py       Cookies manuell importieren → cookies.json
  ./import_and_clone.sh     Import + Klon in einem Schritt
  ./clone.sh                Klon mit cookies.json
  ./clone.sh --interactive  Manueller Playwright-Klon (Opera GX sichtbar)
  ./capture_xl_manual.sh    XL manuell: Opera GX → Refresh → Extension

Extension einmalig laden: opera://extensions → Entwicklermodus → Ordner extension/

Ausgabe: $SITES/
EOF
}

case "$MODE" in
  -h|--help|help)
    show_help
    ;;
  --interactive|-i)
    run_interactive_clone || true
    ;;
  --goclone)
    run_goclone_assets
    run_cookie_clone || run_interactive_clone || true
    ;;
  "")
    if [ -f "$ROOT/cookies.json" ]; then
      echo "=== Klon mit cookies.json ==="
      run_cookie_clone || true
    else
      echo "Keine cookies.json gefunden."
      echo ""
      echo "Manuell (empfohlen):"
      echo "  1. Cookie-Editor Extension → JSON exportieren"
      echo "  2. In cookies_raw.json speichern"
      echo "  3. ./import_and_clone.sh"
      echo ""
      echo "Oder automatisch: ./start_listener.sh + Extension"
      echo "Oder interaktiv:  ./clone.sh --interactive"
      exit 1
    fi
    ;;
  *)
    echo "Unbekannte Option: $MODE"
    show_help
    exit 1
    ;;
esac

echo ""
echo "=== Fertig. Ausgabe: $SITES/ ==="
echo "Vorschau: ./serve.sh"
