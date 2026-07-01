#!/bin/bash
# RTW komplett: Browser-Assets + Replit-Export
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=== 1/3 Browser-Asset-Download (183 Produkte + Kategorie) ==="
echo "Opera GX sichtbar — VPN (DE) muss an sein."
python3 browser_download_assets.py --products-only --headed

echo ""
echo "=== 2/3 Kategorie + Homepage ==="
python3 browser_download_assets.py --target herren/ready-to-wear/vollstandige-ready-to-wear --headed
python3 browser_download_assets.py --target homepage --headed

echo ""
echo "=== 3/3 Replit-Export bauen ==="
python3 prepare_replit_export.py

echo ""
echo "Fertig: replit-export/"
echo "GitHub: cd replit-export && git init && git add . && git commit -m 'LV RTW offline clone'"
