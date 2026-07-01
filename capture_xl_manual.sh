#!/bin/bash
# XL manuell: Opera GX öffnen → Refresh → Extension speichert
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=vpn_utils.sh
source "$ROOT/vpn_utils.sh"

BROWSER="${BROWSER:-opera-gx}"
EXT_URL=$(browser_extensions_url)
URL="https://de.louisvuitton.com/deu-de/herren/ready-to-wear/t-shirts-und-poloshirts/_/N-to9uy2xl"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  XL-Kategorie — Manuell (Opera GX → Refresh → Speichern) ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
show_ip || true
echo "Browser: $BROWSER"
echo ""

if ! vpn_connected; then
  echo "⚠ Bitte ProtonVPN verbinden (Deutschland), dann Enter."
  read -r -p "Enter … " || true
fi

LISTENER_PID=""
if ! curl -sf http://127.0.0.1:8765/health >/dev/null 2>&1; then
  echo "Starte Listener …"
  python3 "$ROOT/cookie_listener.py" &
  LISTENER_PID=$!
  sleep 2
else
  echo "Listener läuft: http://127.0.0.1:8765"
fi

echo ""
echo "Extension einmalig in Opera GX laden:"
echo "  1. $EXT_URL öffnen"
echo "  2. Entwicklermodus aktivieren"
echo "  3. „Entpackte Erweiterung laden“ → Ordner:"
echo "     $ROOT/extension"
echo ""
echo "Dann auf der LV-Seite:"
echo "  1. URL wird jetzt in Opera GX geöffnet"
echo "  2. Warten bis Seite lädt"
echo "  3. F5 / Refresh"
echo "  4. Extension-Icon klicken (Badge ✓ = gespeichert)"
echo ""
echo "URL: $URL"
echo ""

if ! open_browser_url "$URL"; then
  echo ""
  echo "Falls Opera GX schon offen ist: neues Tab, Cmd+V, Enter."
fi

echo ""
echo "Dashboard: http://127.0.0.1:8765"
echo "Warte auf Speicherung … (Ctrl+C zum Beenden)"
echo ""

while true; do
  if [ -f "$ROOT/sites/kategorie/t-shirts-und-poloshirts-xl/index.html" ]; then
    SIZE=$(wc -c < "$ROOT/sites/kategorie/t-shirts-und-poloshirts-xl/index.html" | tr -d ' ')
    if [ "$SIZE" -gt 50000 ]; then
      echo ""
      echo "✓ Gespeichert: ${SIZE} Bytes"
      grep ^title= "$ROOT/sites/kategorie/t-shirts-und-poloshirts-xl/status.txt" 2>/dev/null || true
      echo ""
      echo "Starten: ./start_local.sh"
      [ -n "$LISTENER_PID" ] && kill "$LISTENER_PID" 2>/dev/null || true
      exit 0
    fi
  fi
  sleep 3
done
