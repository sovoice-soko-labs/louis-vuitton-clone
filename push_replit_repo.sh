#!/bin/bash
# Replit-Export nach GitHub pushen (neues Repo)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

REPO_NAME="${REPO_NAME:-louis-vuitton-rtw-replit}"
ORG="${GITHUB_ORG:-sovoice-soko-labs}"
REMOTE="https://github.com/${ORG}/${REPO_NAME}.git"

echo "=== Replit-Export bauen ==="
python3 prepare_replit_export.py

cd replit-export

if [ ! -d .git ]; then
  git init -b main
fi

git add -A
if git diff --cached --quiet; then
  echo "Keine Änderungen zum Committen."
else
  git commit -m "$(cat <<'EOF'
LV Herren Ready-to-Wear Offline-Klon für Replit.

183 Produktseiten mit HTML und lokalen Assets, Kategorie-Listing, Static-Server.
EOF
)"
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Push zu origin …"
  git push -u origin main
else
  git remote add origin "$REMOTE" 2>/dev/null || git remote set-url origin "$REMOTE"
  echo ""
  echo "Neues Repo anlegen: https://github.com/new"
  echo "  Name: ${REPO_NAME}"
  echo "  Org:  ${ORG}"
  echo ""
  echo "Dann: git push -u origin main"
  echo "  (aus $(pwd))"
  if command -v gh >/dev/null 2>&1; then
    gh repo create "${ORG}/${REPO_NAME}" --public --source=. --remote=origin --push
  fi
fi
