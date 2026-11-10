"""Entry point used by both workflows: tracked-file boundary, then the edition's own checks."""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import privacy_boundary  # noqa: E402

privacy_boundary.verify()
runpy.run_path(str(ROOT / "plan" / "model" / "verify.py"), run_name="__main__")
