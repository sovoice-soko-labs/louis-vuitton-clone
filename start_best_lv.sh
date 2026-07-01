#!/bin/bash
# Startet den bestbewerteten LV-Static-Clone aus den Tests
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${1:-3001}"
REPO="$ROOT/repo-tests/Rahul-AkaVector__Louis_Vuitton"

if [ ! -d "$REPO" ]; then
  echo "Repo fehlt. Bitte zuerst: python3 test_all_repos.py"
  exit 1
fi

cd "$REPO"
echo "Rahul-AkaVector/Louis_Vuitton (26★)"
echo "http://localhost:$PORT"
exec python3 -m http.server "$PORT"
