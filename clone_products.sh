#!/bin/bash
# Produkte nacheinander in Opera GX öffnen — du klickst nur F5 + Extension.
# Kein Playwright, kein Bot — deshalb nicht geblockt.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=vpn_utils.sh
source "$ROOT/vpn_utils.sh"

DELAY="${DELAY:-12}"          # Pause zwischen Produkten (Sekunden)
WAIT="${WAIT:-90}"            # Max. Wartezeit pro Produkt
MIN_BYTES="${MIN_BYTES:-50000}"
QUEUE="$ROOT/products_queue.json"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Produkte klonen — langsam & sicher (Opera GX)            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

python3 "$ROOT/extract_products.py" || exit 1
echo ""

if ! curl -sf http://127.0.0.1:8765/health >/dev/null 2>&1; then
  echo "Starte Listener …"
  python3 "$ROOT/cookie_listener.py" &
  sleep 2
fi

echo "Voraussetzungen:"
echo "  • ProtonVPN (Deutschland) an"
echo "  • Extension „LV Seite speichern“ in Opera GX aktiv"
echo "  • Listener: http://127.0.0.1:8765"
echo ""
echo "Pro Produkt: Seite lädt → F5 → Extension → „Seite jetzt speichern“"
echo "Pause zwischen Produkten: ${DELAY}s"
echo ""
read -r -p "Enter zum Starten … " || true

TOTAL=$(python3 -c "import json; d=json.load(open('$QUEUE')); print(d['total'])")
DONE=$(python3 -c "import json; d=json.load(open('$QUEUE')); print(d['saved'])")

while IFS= read -r line; do
  SKU=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['sku'])")
  URL=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")
  DEST="$ROOT/sites/produkte/$SKU/index.html"

  if [ -f "$DEST" ] && [ "$(wc -c < "$DEST" | tr -d ' ')" -gt "$MIN_BYTES" ]; then
    continue
  fi

  DONE=$((DONE + 1))
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  [$DONE/$TOTAL] $SKU"
  echo "  $URL"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  open_browser_url "$URL" || true

  SEC=0
  while [ "$SEC" -lt "$WAIT" ]; do
    if [ -f "$DEST" ] && [ "$(wc -c < "$DEST" | tr -d ' ')" -gt "$MIN_BYTES" ]; then
      echo "  ✓ Gespeichert ($(wc -c < "$DEST" | tr -d ' ') Bytes)"
      python3 "$ROOT/extract_products.py" --status >/dev/null 2>&1 || true
      python3 "$ROOT/close_lv_windows.py" 2>/dev/null || true
      break
    fi
    sleep 2
    SEC=$((SEC + 2))
  done

  if [ ! -f "$DEST" ] || [ "$(wc -c < "$DEST" | tr -d ' ')" -le "$MIN_BYTES" ]; then
    echo "  ⚠ Noch nicht gespeichert — übersprungen (später erneut starten)"
  fi

  echo "  Pause ${DELAY}s …"
  sleep "$DELAY"
done < <(python3 -c "
import json
d=json.load(open('$QUEUE'))
for p in d['products']:
    if not p.get('saved'):
        print(json.dumps(p))
")

python3 "$ROOT/extract_products.py" --status
echo ""
echo "Fertig für diesen Lauf. Erneut starten für fehlende: ./clone_products.sh"
