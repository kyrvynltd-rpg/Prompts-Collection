"""Back up the SQLite database: python scripts/backup.py [destination_dir]. For Postgres use the provider's backups or pg_dump."""
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db import get_db  # noqa: E402


def backup(dest_dir: str = "backups") -> Path:
    db = get_db()
    if db.is_postgres:
        raise SystemExit("Postgres: use your provider's automated backups or pg_dump (see docs/BACKUP_RESTORE.md).")
    out = Path(dest_dir)
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"promptlab-{time.strftime('%Y%m%d-%H%M%S')}.db"
    with sqlite3.connect(target) as dest:
        db._conn.backup(dest)
    target.chmod(0o600)
    return target


if __name__ == "__main__":
    print(backup(*sys.argv[1:2]))
