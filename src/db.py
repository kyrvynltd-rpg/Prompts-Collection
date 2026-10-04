"""Database layer: SQLite by default, Postgres (Supabase, Neon, Render...) when DATABASE_URL is set.

One tiny interface so the rest of the app never cares which one is running. SQL is written with `?`
placeholders and ids are text, so the same statements run on both engines. Schema changes are numbered
migrations applied once, in order.
"""
from __future__ import annotations

import os
import sqlite3
from collections.abc import Sequence
from typing import Any

MIGRATIONS: list[str] = [
    # 1: accounts
    """
    CREATE TABLE users (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        pw_hash TEXT NOT NULL,
        display_name TEXT NOT NULL DEFAULT '',
        created_at BIGINT NOT NULL,
        email_verified_at BIGINT,
        student_domain TEXT,
        student_verified_at BIGINT,
        deleted_at BIGINT
    );
    CREATE TABLE sessions (
        token_hash TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at BIGINT NOT NULL,
        expires_at BIGINT NOT NULL
    );
    CREATE TABLE email_tokens (
        token_hash TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        purpose TEXT NOT NULL,
        expires_at BIGINT NOT NULL,
        used_at BIGINT
    );
    CREATE TABLE login_attempts (
        email TEXT NOT NULL,
        attempted_at BIGINT NOT NULL,
        ok INTEGER NOT NULL
    );
    """,
    # 2: learning progress and favourites
    """
    CREATE TABLE progress (
        user_id TEXT NOT NULL,
        exercise_id TEXT NOT NULL,
        best_score INTEGER NOT NULL,
        attempts INTEGER NOT NULL,
        passed INTEGER NOT NULL,
        updated_at BIGINT NOT NULL,
        PRIMARY KEY (user_id, exercise_id)
    );
    CREATE TABLE favourites (
        user_id TEXT NOT NULL,
        prompt_id TEXT NOT NULL,
        PRIMARY KEY (user_id, prompt_id)
    );
    """,
    # 3: payments
    """
    CREATE TABLE grants (
        subject TEXT PRIMARY KEY,
        plan TEXT NOT NULL,
        expires_at BIGINT NOT NULL
    );
    CREATE TABLE events (
        id TEXT PRIMARY KEY,
        received_at BIGINT NOT NULL
    );
    CREATE TABLE customers (
        provider_customer TEXT PRIMARY KEY,
        user_id TEXT NOT NULL
    );
    """,
    # 4: Pro features
    """
    CREATE TABLE workspace_prompts (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        tags TEXT NOT NULL DEFAULT '',
        created_at BIGINT NOT NULL,
        updated_at BIGINT NOT NULL
    );
    CREATE TABLE ai_usage (
        user_id TEXT NOT NULL,
        month TEXT NOT NULL,
        count INTEGER NOT NULL,
        PRIMARY KEY (user_id, month)
    );
    """,
]


class Database:
    def __init__(self, url: str | None = None):
        url = url if url is not None else (os.getenv("DATABASE_URL") or os.getenv("APP_DB_PATH") or "promptlab.db")
        self.url = url
        self.is_postgres = url.startswith(("postgres://", "postgresql://"))
        self._conn: Any
        if self.is_postgres:
            try:
                import psycopg
            except ImportError as exc:  # pragma: no cover - needs the optional dependency
                raise RuntimeError("Postgres needs: pip install -r requirements-postgres.txt") from exc
            self._conn = psycopg.connect(url)  # pragma: no cover
        else:
            self._conn = sqlite3.connect(url, check_same_thread=False)
        self.migrate()

    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.is_postgres else sql

    def execute(self, sql: str, params: Sequence[Any] = ()) -> Any:
        cur = self._conn.cursor()
        cur.execute(self._sql(sql), tuple(params))
        return cur

    def one(self, sql: str, params: Sequence[Any] = ()) -> tuple | None:
        return self.execute(sql, params).fetchone()

    def all(self, sql: str, params: Sequence[Any] = ()) -> list[tuple]:
        return list(self.execute(sql, params).fetchall())

    def commit(self) -> None:
        self._conn.commit()

    def migrate(self) -> int:
        self.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
        row = self.one("SELECT MAX(version) FROM schema_version")
        current = row[0] if row and row[0] is not None else 0
        for number, script in enumerate(MIGRATIONS, start=1):
            if number <= current:
                continue
            for statement in script.split(";"):
                if statement.strip():
                    self.execute(statement)
            self.execute("INSERT INTO schema_version (version) VALUES (?)", (number,))
            self.commit()
        return len(MIGRATIONS)

    def close(self) -> None:
        self._conn.close()


_shared: Database | None = None


def get_db() -> Database:
    """Process-wide database (one connection). Tests build their own Database(':memory:')."""
    global _shared
    if _shared is None:
        _shared = Database()
    return _shared
