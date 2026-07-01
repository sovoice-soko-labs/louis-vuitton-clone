#!/bin/bash
# Lokaler Server für alle geklonten LV-Seiten
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${1:-5000}"

cd "$ROOT/sites"

if curl -sf "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then
  echo "Server läuft bereits: http://localhost:$PORT/"
  exit 0
fi

if lsof -ti ":$PORT" >/dev/null 2>&1; then
  echo "Port $PORT belegt — beende alten Prozess …"
  lsof -ti ":$PORT" | xargs kill 2>/dev/null || true
  sleep 1
fi

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Louis Vuitton — Lokaler Klon                            ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Übersicht:  http://localhost:$PORT/                          ║"
echo "║  Ready-to-Wear: http://localhost:$PORT/herren/ready-to-wear/   ║"
echo "║  Homepage:   http://localhost:$PORT/homepage/                   ║"
echo "║  Produkt 1:  http://localhost:$PORT/produkte/1AHVYE/          ║"
echo "║  Produkt 2:  http://localhost:$PORT/produkte/1AHVYO/          ║"
echo "║  Kategorie:  http://localhost:$PORT/kategorie/t-shirts-und-poloshirts/"
echo "║  Kategorie XL: http://localhost:$PORT/kategorie/t-shirts-und-poloshirts-xl/"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Beenden: Ctrl+C"
echo ""

exec python3 -m http.server "$PORT"
