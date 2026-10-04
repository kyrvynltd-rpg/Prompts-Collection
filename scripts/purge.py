"""Run retention purge: python scripts/purge.py  (schedule daily; uses DATABASE_URL or APP_DB_PATH)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db import get_db  # noqa: E402
from retention import purge  # noqa: E402

if __name__ == "__main__":
    print(purge(get_db()))
