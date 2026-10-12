import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for relative in ("guardrails",):
    candidate = PROJECT_ROOT / relative
    if candidate.exists():
        sys.path.insert(0, str(candidate))
