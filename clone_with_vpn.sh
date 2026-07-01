#!/bin/bash
# Louis Vuitton klonen mit Proton VPN
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=vpn_utils.sh
source "$ROOT/vpn_utils.sh"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  LV Klon mit Proton VPN                                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "=== Aktuelle Verbindung ==="
show_ip
echo ""

if ! vpn_connected; then
  echo "Proton VPN ist NICHT verbunden."
  echo ""
  echo "Bitte in der ProtonVPN-App:"
  echo "  1. Mit Deutschland (DE) oder Schweiz (CH) verbinden"
  echo "  2. Kein Secure Core (oft blockiert)"
  echo "  3. Plus-Server bevorzugen"
  echo ""
  echo "Versuche automatische Verbindung …"
  if ! vpn_connect; then
    echo ""
    echo "Automatisch fehlgeschlagen."
    echo "Bitte manuell in ProtonVPN verbinden, dann Enter drücken."
    read -r -p "Enter wenn VPN aktiv ist … "
  fi
fi

echo ""
echo "=== Nach VPN-Verbindung ==="
show_ip
echo ""

# Cookies importieren falls vorhanden
if [ -f "$ROOT/cookies_raw.json" ] && [ ! -f "$ROOT/cookies.json" ]; then
  python3 "$ROOT/import_cookies.py" "$ROOT/cookies_raw.json" || true
fi

ensure_pw() {
  if ! python3 -c "import playwright" 2>/dev/null; then
    pip3 install --user playwright
  fi
  python3 -m playwright install chromium 2>/dev/null || true
}

echo "=== Methode 1: Playwright + Cookies (Chrome sichtbar) ==="
ensure_pw

if [ -f "$ROOT/cookies.json" ]; then
  python3 "$ROOT/browser_clone.py" --cookies-only --headed --auto || true
else
  echo "Keine cookies.json — interaktiver Modus"
  python3 "$ROOT/browser_clone.py" --headed || true
fi

BLOCKED=$(grep -rl "blocked=True" "$ROOT/sites"/*/status.txt 2>/dev/null | wc -l | tr -d ' ')
OK=$(grep -rl "blocked=False" "$ROOT/sites"/*/status.txt 2>/dev/null | wc -l | tr -d ' ')

echo ""
if [ "$OK" -gt 0 ] 2>/dev/null; then
  echo "✓ $OK Seite(n) erfolgreich geklont → sites/"
  echo "Vorschau: ./serve.sh"
else
  echo "Playwright weiter blockiert."
  echo ""
  echo "=== Methode 2: Extension (zuverlässigste) ==="
  echo "  Terminal 1: ./start_listener.sh"
  echo "  Chrome: Extension v1.2 laden, LV-Seiten besuchen"
  echo "  Extension-Icon klicken = Seite speichern"
fi

echo ""
echo "=== Fertig ==="
