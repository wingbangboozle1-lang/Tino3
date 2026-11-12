#!/usr/bin/env python3
"""Set the precision at which assessment-roll values and tax bills are published.

    python3 scripts/privacy_tier.py 1|2|3
    python3 scripts/model.py && python3 scripts/build.py

Tier 1 is the owner's instruction of 12 November 2026: roll values to the nearest $10.
Tier 2 rounds them to the nearest $1,000 and tier 3 to the nearest $10,000. The tier is stored in
assets/privacy.json, which is committed, so the build and the checks reproduce the same pages.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "assets" / "privacy.json"

if len(sys.argv) != 2 or sys.argv[1] not in {"1", "2", "3"}:
    raise SystemExit(__doc__)
cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
cfg["tier"] = int(sys.argv[1])
CONFIG.write_text(json.dumps(cfg, indent=1) + "\n", encoding="utf-8")
print(f"privacy tier set to {cfg['tier']}: {cfg['tiers'][sys.argv[1]]}. "
      f"Now run scripts/model.py, scripts/build.py and scripts/verify.py.")
