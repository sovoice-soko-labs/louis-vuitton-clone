#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OK=0
FAIL=0

pass() { echo "  ✓ $1"; OK=$((OK + 1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }
info() { echo "  ○ $1"; }

echo "=== Louis Vuitton Klon — Systemcheck ==="
echo ""

echo "Dateien:"
test -x "$ROOT/goclone" && pass "goclone Binary" || fail "goclone Binary"
test -f "$ROOT/browser_clone.py" && pass "browser_clone.py" || fail "browser_clone.py"
test -f "$ROOT/cookie_listener.py" && pass "cookie_listener.py" || fail "cookie_listener.py"
test -f "$ROOT/extension/manifest.json" && pass "Extension manifest" || fail "Extension manifest"
test -f "$ROOT/extension/background.js" && pass "Extension background.js" || fail "Extension background.js"

echo ""
echo "Python:"
python3 -c "import playwright" 2>/dev/null && pass "playwright Modul" || fail "playwright Modul"
python3 -c "import ast; ast.parse(open('$ROOT/browser_clone.py').read())" 2>/dev/null \
  && pass "browser_clone.py Syntax" || fail "browser_clone.py Syntax"
python3 -c "import ast; ast.parse(open('$ROOT/cookie_listener.py').read())" 2>/dev/null \
  && pass "cookie_listener.py Syntax" || fail "cookie_listener.py Syntax"

echo ""
echo "Cookies & Ausgabe:"
if [ -f "$ROOT/cookies.json" ]; then
  COUNT=$(python3 -c "import json; print(len(json.load(open('$ROOT/cookies.json'))))")
  pass "cookies.json ($COUNT Cookies)"
else
  info "cookies.json (noch nicht — Extension/Listener nötig)"
fi

PAGES=$(find "$ROOT/sites" -name index.html 2>/dev/null | wc -l | tr -d ' ')
info "sites/ ($PAGES index.html — aktuell vermutlich Access-denied-Platzhalter)"

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "Alles bereit ($OK Checks OK)."
  echo "Nächster Schritt: ./start_listener.sh"
else
  echo "$FAIL Problem(e). Fix: pip3 install --user playwright && python3 -m playwright install chromium"
  exit 1
fi
