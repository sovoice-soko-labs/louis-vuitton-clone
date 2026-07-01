#!/bin/bash
# VPN-Hilfsfunktionen für Proton VPN (macOS)
set -euo pipefail

VPN_NAME="${VPN_NAME:-ProtonVPN}"

get_ip() {
  curl -s --max-time 10 https://ipinfo.io/json 2>/dev/null || echo '{}'
}

vpn_status() {
  scutil --nc status "$VPN_NAME" 2>/dev/null | head -1 || echo "Unknown"
}

vpn_connected() {
  vpn_status | grep -qi "Connected"
}

vpn_connect() {
  if vpn_connected; then
    echo "ProtonVPN bereits verbunden."
    return 0
  fi
  echo "Starte ProtonVPN …"
  open -a "ProtonVPN" 2>/dev/null || true
  sleep 2
  scutil --nc start "$VPN_NAME" 2>/dev/null || true
  for i in $(seq 1 30); do
    if vpn_connected; then
      echo "ProtonVPN verbunden."
      return 0
    fi
    sleep 2
  done
  return 1
}

vpn_disconnect() {
  scutil --nc stop "$VPN_NAME" 2>/dev/null || true
}

show_ip() {
  local info ip city country org
  info=$(get_ip)
  ip=$(echo "$info" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ip','?'))" 2>/dev/null || echo "?")
  city=$(echo "$info" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('city',''))" 2>/dev/null || echo "")
  country=$(echo "$info" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('country',''))" 2>/dev/null || echo "")
  org=$(echo "$info" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('org',''))" 2>/dev/null || echo "")
  echo "IP:      $ip"
  echo "Ort:     $city, $country"
  echo "Anbieter: $org"
  echo "VPN:     $(vpn_status)"
}

# Browser-Hilfsfunktionen (Opera GX bevorzugt, Chrome optional)
BROWSER="${BROWSER:-opera-gx}"

browser_paths() {
  case "$BROWSER" in
    opera-gx|operagx|opera)
      echo "/Applications/Opera GX.app|Opera|Opera GX"
      ;;
    chrome|google-chrome)
      echo "/Applications/Google Chrome.app|Google Chrome|Google Chrome"
      ;;
    auto)
      if [ -d "/Applications/Opera GX.app" ]; then
        echo "/Applications/Opera GX.app|Opera|Opera GX"
      elif [ -d "/Applications/Google Chrome.app" ]; then
        echo "/Applications/Google Chrome.app|Google Chrome|Google Chrome"
      fi
      ;;
    *)
      echo "/Applications/Opera GX.app|Opera|Opera GX"
      ;;
  esac
}

browser_extensions_url() {
  case "$BROWSER" in
    chrome|google-chrome) echo "chrome://extensions" ;;
    *) echo "opera://extensions" ;;
  esac
}

open_browser_url() {
  local url="$1"
  local info app bin name
  info=$(browser_paths)
  [ -z "$info" ] && { echo "FEHLER: Kein Browser gefunden."; return 1; }

  app="${info%%|*}"
  bin="${info#*|}"; bin="${bin%%|*}"
  name="${info##*|}"
  local binary="$app/Contents/MacOS/$bin"

  if [ ! -d "$app" ]; then
    echo "FEHLER: $name nicht gefunden unter $app"
    echo "Tipp: BROWSER=chrome ./capture_xl_manual.sh"
    return 1
  fi

  printf '%s' "$url" | pbcopy 2>/dev/null || true

  if [ -x "$binary" ]; then
    # Neuer Tab im bestehenden Fenster (nicht jedes Mal neues Fenster)
    "$binary" "$url" >/dev/null 2>&1 &
    disown 2>/dev/null || true
    sleep 1
    echo "$name: neuer Tab geöffnet."
    return 0
  fi

  if open -a "$app" "$url" 2>/dev/null; then
    echo "$name geöffnet via open."
    return 0
  fi

  echo "$name konnte nicht automatisch geöffnet werden."
  echo "Bitte manuell öffnen und URL einfügen (Cmd+V):"
  echo "  $url"
  return 1
}

# Alias für ältere Scripts
open_chrome_url() { open_browser_url "$@"; }
