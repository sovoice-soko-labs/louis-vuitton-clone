#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 "$ROOT/extract_products.py" --status
python3 "$ROOT/close_lv_windows.py" "$@"
