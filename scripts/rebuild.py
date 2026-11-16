#!/usr/bin/env python3
"""Rebuild every derived model and page in dependency order.

The model and economic bootstrap have a small dependency cycle: model.py first
computes break-even values consumed by economy.py; model.py then embeds the
refreshed bootstrap distributions from economy.json. mixed.py consumes both final
JSON outputs, liquidity.py consumes model.json and mixed.json (it repriced the
mixed paths for the two-person case), and build.py consumes all model outputs to
write the site, CSV tables, and executive summary.

All generators are deterministic and use only checked-in inputs. Their stdout and
stderr are suppressed so property-specific model diagnostics are not copied into
public CI logs. If a step fails, run the named component locally for diagnostics.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

STEPS = (
    ("model (calculate current paths and break-evens)", "model.py"),
    ("economy (rebuild the bootstrap from the current model)", "economy.py"),
    ("model (embed the refreshed bootstrap)", "model.py"),
    ("mixed paths (use the refreshed model and bootstrap)", "mixed.py"),
    ("estate liquidity and the two-person case", "liquidity.py"),
    ("site and executive summary", "build.py"),
)


def main() -> int:
    for label, script in STEPS:
        print(f"Rebuilding {label}...", flush=True)
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script)],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode:
            raise SystemExit(
                f"Rebuild failed in {script} (exit {result.returncode}); "
                "component output was suppressed. Run that component locally for diagnostics."
            )
    print("Rebuild complete: model, economy, mixed paths, liquidity, pages, tables, and executive summary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
