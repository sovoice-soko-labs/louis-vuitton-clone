#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${1:-5000}"
SITE="${2:-homepage}"

cd "$ROOT/sites/$SITE"
echo "Vorschau: http://localhost:$PORT"
echo "Ordner: sites/$SITE"
exec python3 -m http.server "$PORT"
