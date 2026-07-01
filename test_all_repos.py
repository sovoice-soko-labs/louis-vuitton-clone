#!/usr/bin/env python3
"""Testet GitHub website-clone Repos: klonen, Typ erkennen, Startbarkeit prüfen."""

from typing import Optional
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "repo-tests"
RESULTS = Path(__file__).resolve().parent / "repo-test-results.json"

LV_REPOS_EXTRA = [
    "pkprajapati7402/Louis-Vuitton-Website-Clone",
    "Rahul-AkaVector/Louis_Vuitton",
    "square-story/Louis-Vuitton",
    "jiteshsatija/louisvuitton-clone",
    "ginthozan-v/shopify-louis-vuitton-clone",
    "Ramulas007/LV-Home-tailwind",
    "misab-hussain/Louis-Vuitton-clone",
    "IrfanNisar010/LouisVuittonCloneSite",
]


def fetch_topic_repos() -> list:
    repos = {}
    for page in (1, 2):
        url = (
            "https://api.github.com/search/repositories?"
            f"q=topic:website-clone&sort=stars&per_page=100&page={page}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "lv-clone-tester"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        for r in data.get("items", []):
            repos[r["full_name"]] = {
                "url": r["clone_url"],
                "stars": r.get("stargazers_count", 0),
                "description": r.get("description") or "",
                "language": r.get("language") or "",
            }
    for name in LV_REPOS_EXTRA:
        if name not in repos:
            api = f"https://api.github.com/repos/{name}"
            try:
                req = urllib.request.Request(api, headers={"User-Agent": "lv-clone-tester"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    r = json.loads(resp.read().decode())
                repos[name] = {
                    "url": r["clone_url"],
                    "stars": r.get("stargazers_count", 0),
                    "description": r.get("description") or "",
                    "language": r.get("language") or "",
                }
            except Exception:
                pass
    return repos


def find_entry(repo_dir: Path) -> Optional[Path]:
    candidates = [
        repo_dir / "index.html",
        repo_dir / "public" / "index.html",
        repo_dir / "dist" / "index.html",
        repo_dir / "build" / "index.html",
    ]
    for c in candidates:
        if c.exists():
            return c
    for html in repo_dir.rglob("index.html"):
        if "node_modules" not in str(html):
            return html
    return None


def analyze_repo(name: str, meta: dict) -> dict:
    slug = name.replace("/", "__")
    dest = OUT / slug
    result = {
        "name": name,
        "stars": meta["stars"],
        "language": meta["language"],
        "lv_related": bool(re.search(r"louis.?vuitton|\blv\b", f"{name} {meta['description']}", re.I)),
        "status": "unknown",
        "type": None,
        "entry": None,
        "notes": [],
    }

    if dest.exists():
        shutil.rmtree(dest)

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", meta["url"], str(dest)],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        result["status"] = "clone_timeout"
        return result
    except subprocess.CalledProcessError as exc:
        result["status"] = "clone_failed"
        result["notes"].append((exc.stderr or b"").decode()[:200])
        return result

    pkg = dest / "package.json"
    req = dest / "requirements.txt"
    entry = find_entry(dest)

    if (dest / "go.mod").exists() or name.endswith("Website-Cloner"):
        result["type"] = "go_tool"
        result["status"] = "tool"
    elif pkg.exists():
        result["type"] = "nodejs"
        try:
            pkg_data = json.loads(pkg.read_text())
            scripts = pkg_data.get("scripts", {})
            if entry:
                result["status"] = "static_ready" if not scripts.get("start") else "needs_npm_start"
            elif scripts.get("start") or scripts.get("dev"):
                result["status"] = "needs_npm_install"
            else:
                result["status"] = "nodejs_no_start"
            result["notes"].append(f"scripts: {list(scripts.keys())[:5]}")
        except Exception:
            result["status"] = "nodejs_unknown"
    elif req.exists():
        result["type"] = "python"
        result["status"] = "needs_pip"
    elif entry:
        result["type"] = "static"
        result["status"] = "static_ready"
        result["entry"] = str(entry.relative_to(dest))
    else:
        result["status"] = "no_entry"
        files = list(dest.iterdir())[:8]
        result["notes"].append("files: " + ", ".join(f.name for f in files))

    if entry and result["status"] in ("static_ready", "needs_npm_start"):
        result["entry"] = str(entry.relative_to(dest))

    return result


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    repos = fetch_topic_repos()
    print(f"Teste {len(repos)} Repos …\n")

    results = []
    for i, (name, meta) in enumerate(sorted(repos.items(), key=lambda x: -x[1]["stars"]), 1):
        print(f"[{i}/{len(repos)}] {name} …", flush=True)
        results.append(analyze_repo(name, meta))

    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")

    static = [r for r in results if r["status"] == "static_ready"]
    lv = [r for r in results if r["lv_related"]]
    lv_ready = [r for r in lv if r["status"] == "static_ready"]

    print("\n" + "=" * 60)
    print(f"Gesamt:        {len(results)}")
    print(f"Sofort nutzbar (static): {len(static)}")
    print(f"LV-bezogen:    {len(lv)}")
    print(f"LV sofort nutzbar:       {len(lv_ready)}")
    print(f"Ergebnisse:    {RESULTS}")

    print("\n--- LV Repos ---")
    for r in sorted(lv, key=lambda x: -x["stars"]):
        print(f"  {r['status']:18} {r['name']} ({r['stars']}★)")

    print("\n--- Top static_ready ---")
    for r in sorted(static, key=lambda x: -x["stars"])[:15]:
        print(f"  {r['name']} ({r['stars']}★) → {r.get('entry','index.html')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
