"""
Entrypoint proxy to allow running seed script via `python -m app.seed_data`.
"""
import sys
from pathlib import Path

# Ensure backend root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.seed_data import run_seed

if __name__ == "__main__":
    run_seed()

