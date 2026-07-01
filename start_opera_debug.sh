#!/bin/bash
# Opera GX mit Remote-Debugging — nur nötig wenn --attach noch nicht verbinden kann.
# Bestehendes Opera einmal schließen, dann dieses Script, dann LV-Homepage öffnen.
set -euo pipefail
OPERA="/Applications/Opera GX.app/Contents/MacOS/Opera"
PORT="${CDP_PORT:-9222}"

if [ ! -x "$OPERA" ]; then
  echo "FEHLER: Opera GX nicht gefunden."
  exit 1
fi

if curl -s --max-time 2 "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
  echo "Debug-Port ${PORT} läuft bereits."
  exit 0
fi

echo "Starte Opera GX mit Remote-Debugging auf Port ${PORT} …"
echo "Danach: LV-Homepage öffnen, dann ./scrapling_download.sh attach category"
"$OPERA" --remote-debugging-port="${PORT}" >/dev/null 2>&1 &
disown 2>/dev/null || true
