#!/usr/bin/env python3
"""Replit-Einstieg: startet den Server aus replit-export/."""
import os
import runpy
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.join(ROOT, "replit-export")

if not os.path.isdir(EXPORT):
    print("replit-export/ fehlt — bitte zuerst: python3 prepare_replit_export.py")
    sys.exit(1)

os.chdir(EXPORT)
sys.path.insert(0, EXPORT)
runpy.run_path(os.path.join(EXPORT, "main.py"), run_name="__main__")
