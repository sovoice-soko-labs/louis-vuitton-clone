#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
FILE="${1:-$ROOT/cookies_raw.json}"

python3 "$ROOT/import_cookies.py" "$FILE" && "$ROOT/clone.sh"
