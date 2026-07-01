#!/usr/bin/env python3
"""Lokaler Listener: empfängt Cookies aus Chrome und startet den Klon."""

import argparse
import hashlib
import json
import re
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
COOKIES_FILE = ROOT / "cookies.json"
STATE_FILE = ROOT / ".cookie-listener-state.json"
SITES = ROOT / "sites"
PORT = 8765
HOST = "127.0.0.1"

URL_TO_PATH = [
    ("N-tmfgzj3", "herren/ready-to-wear/vollstandige-ready-to-wear"),
    ("N-to9uy2xl", "kategorie/t-shirts-und-poloshirts-xl"),
    ("N-to9uy2x", "kategorie/t-shirts-und-poloshirts"),
    ("1AHVYO", "produkte/1AHVYO"),
    ("1AHVYE", "produkte/1AHVYE"),
    ("deu-de/homepage", "homepage"),
]

# Hauptziel: gesamte Herren Ready-to-Wear Übersicht
READY_TO_WEAR_PATH = "herren/ready-to-wear"
READY_TO_WEAR_PREFIX = "/deu-de/herren/ready-to-wear"
PRODUCT_PREFIX = "/deu-de/produkte/"
SKU_RE = re.compile(r"^[A-Z0-9]{5,8}$")

_clone_lock = threading.Lock()
_clone_running = False


def chrome_to_playwright(cookies: List[dict]) -> List[dict]:
    same_site_map = {
        "no_restriction": "None",
        "lax": "Lax",
        "strict": "Strict",
        "unspecified": "Lax",
    }
    out: List[dict] = []
    for c in cookies:
        item: Dict[str, Any] = {
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".louisvuitton.com"),
            "path": c.get("path", "/"),
        }
        if c.get("expirationDate"):
            item["expires"] = int(c["expirationDate"])
        if "httpOnly" in c:
            item["httpOnly"] = bool(c["httpOnly"])
        if "secure" in c:
            item["secure"] = bool(c["secure"])
        ss = c.get("sameSite")
        if ss in same_site_map:
            item["sameSite"] = same_site_map[ss]
        elif ss in ("Lax", "Strict", "None"):
            item["sameSite"] = ss
        out.append(item)
    return out


def cookie_fingerprint(cookies: List[dict]) -> str:
    payload = sorted((c.get("name", ""), c.get("value", "")) for c in cookies)
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()[:16]


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def run_clone() -> None:
    global _clone_running
    with _clone_lock:
        if _clone_running:
            return
        _clone_running = True

    def worker() -> None:
        global _clone_running
        state = load_state()
        state["clone_status"] = "running"
        state["clone_started_at"] = datetime.now().isoformat(timespec="seconds")
        save_state(state)
        try:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "browser_clone.py"), "--auto", "--cookies-only"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            state = load_state()
            state["clone_status"] = "done" if proc.returncode == 0 else "failed"
            state["clone_finished_at"] = datetime.now().isoformat(timespec="seconds")
            state["clone_exit_code"] = proc.returncode
            state["clone_log"] = (proc.stdout or "")[-4000:]
            if proc.stderr:
                state["clone_log"] += "\n" + proc.stderr[-2000:]
            save_state(state)
            print(f"\n[Klon] beendet (exit {proc.returncode})")
            if proc.stdout:
                print(proc.stdout[-2000:])
        finally:
            with _clone_lock:
                _clone_running = False

    threading.Thread(target=worker, daemon=True).start()


def handle_cookies(payload: dict, auto_clone: bool) -> dict:
    raw = payload.get("cookies", [])
    if not raw:
        raise ValueError("Keine Cookies im Request")

    pw_cookies = chrome_to_playwright(raw)
    fp = cookie_fingerprint(raw)
    state = load_state()

    if state.get("fingerprint") == fp:
        return {
            "ok": True,
            "message": "Cookies unverändert — kein neuer Klon",
            "count": len(pw_cookies),
            "skipped": True,
        }

    COOKIES_FILE.write_text(json.dumps(pw_cookies, indent=2), encoding="utf-8")
    state.update(
        {
            "fingerprint": fp,
            "cookie_count": len(pw_cookies),
            "captured_at": datetime.now().isoformat(timespec="seconds"),
            "source_url": payload.get("url", ""),
            "last_reason": payload.get("reason", ""),
            "clone_status": state.get("clone_status", "idle"),
        }
    )
    save_state(state)
    print(f"\n[Listener] {len(pw_cookies)} Cookies gespeichert → cookies.json")
    if payload.get("url"):
        print(f"           Quelle: {payload['url']}")

    if auto_clone:
        print("[Listener] Starte Klon …")
        run_clone()
        message = f"{len(pw_cookies)} Cookies gespeichert, Klon gestartet"
    else:
        message = f"{len(pw_cookies)} Cookies gespeichert"

    return {"ok": True, "message": message, "count": len(pw_cookies), "skipped": False}


def url_to_path(url: str) -> Optional[str]:
    for key, path in URL_TO_PATH:
        if key in url:
            return path

    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    if path.startswith(PRODUCT_PREFIX):
        sku = path.rsplit("/", 1)[-1]
        if SKU_RE.match(sku):
            return f"produkte/{sku}"

    if not path.startswith(READY_TO_WEAR_PREFIX):
        return None

    if path == READY_TO_WEAR_PREFIX:
        return READY_TO_WEAR_PATH

    suffix = path[len(READY_TO_WEAR_PREFIX) :].strip("/")
    if suffix:
        slug = suffix.split("/")[0].split("_")[0]
        if slug:
            return f"{READY_TO_WEAR_PATH}/{slug}"

    return None


def handle_save_page(payload: dict) -> dict:
    url = payload.get("url", "")
    html = payload.get("html", "")
    title = payload.get("title", "")

    if not html:
        raise ValueError("Kein HTML im Request")
    if len(html) < 50_000:
        raise ValueError(f"HTML zu klein ({len(html)} Bytes) — bitte nach Refresh erneut speichern")
    if "Access denied" in html or "Accès refusé" in html:
        raise ValueError("Seite ist blockiert (Access denied)")
    if "Fehler aufgetreten" in title or "Fehler aufgetreten" in html[:5000]:
        raise ValueError("LV-Fehlerseite — bitte F5 drücken und erneut speichern")

    rel = url_to_path(url)
    if not rel:
        raise ValueError(f"URL nicht in Ziel-Liste: {url}")

    dest = SITES / rel
    dest.mkdir(parents=True, exist_ok=True)
    for sub in ("css", "js", "imgs"):
        (dest / sub).mkdir(exist_ok=True)

    (dest / "index.html").write_text(html, encoding="utf-8")
    (dest / "status.txt").write_text(
        f"url={url}\ntitle={title}\nblocked=False\nsource=browser-extension\n",
        encoding="utf-8",
    )

    state = load_state()
    saved = state.get("saved_pages", {})
    saved[rel] = datetime.now().isoformat(timespec="seconds")
    state["saved_pages"] = saved
    state["last_page_save"] = rel
    save_state(state)

    print(f"[POST /save-page] Gespeichert: sites/{rel} ({len(html)} bytes)")
    return {"ok": True, "message": f"Gespeichert: {rel}", "path": rel}


class ListenerHandler(BaseHTTPRequestHandler):
    server_version = "LVCookieListener/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"ok": True, "port": PORT})
            return

        if self.path == "/status":
            self._json(200, load_state())
            return

        state = load_state()
        ext_ok = state.get("cookie_count", 0) > 0
        saved = state.get("saved_pages", {})
        saved_list = "".join(f"<li><code>{k}</code> — {v}</li>" for k, v in saved.items()) or "<li>—</li>"
        html = f"""<!DOCTYPE html>
<html lang="de"><head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="5">
<title>LV Cookie Listener</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 680px; margin: 2rem auto; padding: 0 1rem; }}
  .ok {{ color: #0a0; }} .warn {{ color: #a60; }}
  code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
</style>
</head><body>
<h1>LV Cookie Listener</h1>
<ul>
  <li>Cookies: <strong>{state.get('cookie_count', 0)}</strong></li>
  <li>Gespeicherte Seiten: <strong>{len(saved)}/5</strong></li>
</ul>
<h2>Gespeichert</h2>
<ul>{saved_list}</ul>
<h2>Anleitung</h2>
<ol>
  <li>Extension laden in <code>opera://extensions</code> (Opera GX) oder <code>chrome://extensions</code></li>
  <li>Listener läuft — jede LV-Zielseite in Opera GX besuchen</li>
  <li>Extension-Icon klicken = aktuelle Seite speichern</li>
</ol>
<p>Ziel-URLs nacheinander öffnen (5 Seiten).</p>
</body></html>"""
        self._html(html)

    def _route(self) -> str:
        return self.path.split("?", 1)[0].rstrip("/") or "/"

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "error": "Ungültiges JSON"})
            return

        route = self._route()

        if route == "/cookies":
            try:
                auto_clone = payload.get("auto_clone", False)
                reason = payload.get("reason", "?")
                count_in = len(payload.get("cookies", []))
                print(f"[POST /cookies] {count_in} Cookies ({reason}) von {self.client_address[0]}")
                result = handle_cookies(payload, auto_clone=auto_clone)
                self._json(200, result)
            except ValueError as exc:
                self._json(400, {"ok": False, "error": str(exc)})
            return

        if route == "/save-page":
            try:
                result = handle_save_page(payload)
                self._json(200, result)
            except ValueError as exc:
                self._json(400, {"ok": False, "error": str(exc)})
            return

        if route == "/clone":
            if not COOKIES_FILE.exists():
                self._json(400, {"ok": False, "error": "cookies.json fehlt"})
                return
            run_clone()
            self._json(200, {"ok": True, "message": "Klon gestartet"})
            return

        self._json(404, {"ok": False, "error": f"Unbekannte Route: {route}"})


class ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True


def listener_running(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/health", timeout=1) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def free_port(port: int) -> None:
    """Beendet Prozess auf Port, falls es unser alter Listener ist."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False,
        )
        pids = [p.strip() for p in result.stdout.splitlines() if p.strip()]
        for pid in pids:
            subprocess.run(["kill", pid], check=False)
        if pids:
            print(f"Alter Prozess auf Port {port} beendet.")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Cookie-Listener für Louis Vuitton Klon")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--no-auto-clone", action="store_true")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  LV Cookie Listener                                      ║
╠══════════════════════════════════════════════════════════╣
║  1. Extension laden: opera://extensions (Opera GX)         ║
║     → Entwicklermodus → Ordner: extension/               ║
║  2. LV-Seiten in Opera GX öffnen (echte Seite sichtbar) ║
║  3. Extension speichert HTML nach Refresh (v1.4)         ║
╠══════════════════════════════════════════════════════════╣
║  Dashboard: http://{HOST}:{args.port:<5}                        ║
╚══════════════════════════════════════════════════════════╝
""")
    if listener_running(args.port):
        print(f"Listener läuft bereits → http://{HOST}:{args.port}")
        print("Extension kann Cookies senden. Kein Neustart nötig.")
        return

    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.settimeout(0.5)
        in_use = probe.connect_ex((HOST, args.port)) == 0
        probe.close()
    except OSError:
        in_use = False

    if in_use:
        print(f"Port {args.port} ist belegt — versuche freizugeben …")
        free_port(args.port)

    server = ReuseHTTPServer((HOST, args.port), ListenerHandler)
    try:
        server.serve_forever()
    except OSError as exc:
        if getattr(exc, "errno", None) == 48:
            print(
                f"\nFEHLER: Port {args.port} noch belegt.\n"
                f"  ./stop_listener.sh\n"
                f"  oder: lsof -ti :{args.port} | xargs kill\n",
                file=sys.stderr,
            )
            sys.exit(1)
        raise
    except KeyboardInterrupt:
        print("\nListener beendet.")
        server.server_close()


if __name__ == "__main__":
    main()
