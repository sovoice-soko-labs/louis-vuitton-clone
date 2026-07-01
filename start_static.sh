#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${1:-3000}"
cd "$ROOT/static-clone"
echo "Louis Vuitton Static Clone"
echo "Quelle: https://github.com/pkprajapati7402/Louis-Vuitton-Website-Clone"
echo "Vorschau: http://localhost:$PORT"
exec python3 -m http.server "$PORT"
