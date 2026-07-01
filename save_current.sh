#!/bin/bash
# Passiv: öffnet KEINEN Browser. Du bist schon auf der Seite → F5 → Extension.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGET="${TARGET:-herren/ready-to-wear/vollstandige-ready-to-wear}"
MIN_BYTES="${MIN_BYTES:-50000}"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Seite speichern (nur Refresh + Extension)               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Ziel: sites/$TARGET/"
echo ""
echo "Du bist schon auf der LV-Seite in Opera GX?"
echo "  1. Extension in Opera GX: opera://extensions"
echo "     → „LV Seite speichern“ an Toolbar anheften (Pin-Symbol)"
echo "  2. F5 / Refresh auf der LV-Seite"
echo "  3. Extension-Icon klicken → „Seite jetzt speichern“"
echo "     Grüne Meldung = gespeichert"
echo ""
echo "Extension: opera://extensions → Ordner $ROOT/extension"
echo ""

if ! curl -sf http://127.0.0.1:8765/health >/dev/null 2>&1; then
  echo "Starte Listener …"
  python3 "$ROOT/cookie_listener.py" &
  LISTENER_PID=$!
  sleep 2
else
  echo "Listener: http://127.0.0.1:8765"
  LISTENER_PID=""
fi

DEST="$ROOT/sites/$TARGET/index.html"
echo "Warte auf Speicherung … (Ctrl+C zum Beenden)"
echo ""

while true; do
  if [ -f "$DEST" ]; then
    SIZE=$(wc -c < "$DEST" | tr -d ' ')
    if [ "$SIZE" -gt "$MIN_BYTES" ]; then
      echo ""
      echo "✓ Gespeichert: $DEST ($SIZE Bytes)"
      grep -E '^(title|url)=' "$ROOT/sites/$TARGET/status.txt" 2>/dev/null || true
      echo ""
      echo "Vorschau: ./start_local.sh → http://localhost:5000/$TARGET/"
      [ -n "${LISTENER_PID:-}" ] && kill "$LISTENER_PID" 2>/dev/null || true
      exit 0
    fi
  fi
  sleep 2
done
