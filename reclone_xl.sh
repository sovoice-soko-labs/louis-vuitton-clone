#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/vpn_utils.sh"

echo "=== XL mit Warmup + Refresh (VPN) ==="
show_ip
echo ""

if ! vpn_connected; then
  read -r -p "ProtonVPN verbinden, dann Enter … "
fi

python3 "$ROOT/browser_clone.py" \
  --cookies-only --headed --refresh \
  --only "kategorie/t-shirts-und-poloshirts-xl"
