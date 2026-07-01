#!/bin/bash
# Repo auf GitHub pushen (einmalig)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ -z "${1:-}" ]; then
  echo "Nutzung:"
  echo "  ./publish_to_github.sh https://github.com/DEIN-USER/louis-vuitton-clone.git"
  echo ""
  echo "Vorher auf github.com ein leeres Repo anlegen (ohne README)."
  exit 1
fi

REPO_URL="$1"
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"
git branch -M main
echo "Pushe $(du -sh .git | cut -f1) nach $REPO_URL …"
git push -u origin main
echo ""
echo "Fertig: ${REPO_URL%.git}"
