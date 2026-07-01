#!/bin/bash
# Bilder/CSS/JS für alle gespeicherten Seiten nachladen
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=== 1/2 Kategorie Ready-to-Wear (alle Produktbilder) ==="
python3 download_assets.py --target herren/ready-to-wear/vollstandige-ready-to-wear --delay 0.1

echo ""
echo "=== 2/2 Alle 183 Produktseiten ==="
python3 download_assets.py --products-only --delay 0.1

echo ""
echo "Fertig. Prüfen: ./start_local.sh"
