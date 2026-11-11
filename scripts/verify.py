#!/usr/bin/env python3
"""Compatibility entry point for the privacy-first public-site verification suite."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
raise SystemExit(subprocess.run([sys.executable, "public_site/verify.py"], cwd=ROOT).returncode)
