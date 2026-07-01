#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PORT=8765

if ! python3 -c "import playwright" 2>/dev/null; then
  pip3 install --user playwright
  python3 -m playwright install chromium
fi

if curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
  echo "Listener läuft bereits: http://127.0.0.1:$PORT"
  echo "Extension-Ordner: $ROOT/extension"
  exit 0
fi

if lsof -ti ":$PORT" >/dev/null 2>&1; then
  echo "Port $PORT belegt — räume auf …"
  lsof -ti ":$PORT" | xargs kill 2>/dev/null || true
  sleep 1
fi

echo "Starte Cookie-Listener auf http://127.0.0.1:$PORT"
echo "Extension-Ordner: $ROOT/extension"
echo ""
exec python3 "$ROOT/cookie_listener.py" --port "$PORT"
