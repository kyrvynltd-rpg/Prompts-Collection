"""Pro: a personal prompt workspace (save, edit, delete, export). Plain database rows, scoped to one user."""
from __future__ import annotations

import json
import time
import uuid

from db import Database

MAX_PROMPTS = 500
MAX_BODY = 8000


class WorkspaceError(ValueError):
    pass


class Workspace:
    def __init__(self, db: Database):
        self.db = db

    def save(self, user_id: str, title: str, body: str, tags: str = "", prompt_id: str | None = None, now: float | None = None) -> str:
        now_i = int(now if now is not None else time.time())
        title, body = title.strip()[:120], body.strip()
        if not title or not body:
            raise WorkspaceError("A title and the prompt text are both needed.")
        if len(body) > MAX_BODY:
            raise WorkspaceError(f"Prompts can be up to {MAX_BODY} characters.")
        tags = ",".join(t.strip() for t in tags.split(",") if t.strip())[:200]
        if prompt_id:
            cur = self.db.execute("UPDATE workspace_prompts SET title=?, body=?, tags=?, updated_at=? WHERE id=? AND user_id=?",
                                  (title, body, tags, now_i, prompt_id, user_id))
            if cur.rowcount == 0:
                raise WorkspaceError("Prompt not found.")
            self.db.commit()
            return prompt_id
        if self.db.one("SELECT COUNT(*) FROM workspace_prompts WHERE user_id=?", (user_id,))[0] >= MAX_PROMPTS:  # type: ignore[index]
            raise WorkspaceError("Workspace is full.")
        new_id = uuid.uuid4().hex
        self.db.execute("INSERT INTO workspace_prompts (id, user_id, title, body, tags, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                        (new_id, user_id, title, body, tags, now_i, now_i))
        self.db.commit()
        return new_id

    def list(self, user_id: str, search: str = "") -> list[dict]:
        rows = self.db.all("SELECT id, title, body, tags, updated_at FROM workspace_prompts WHERE user_id=? ORDER BY updated_at DESC", (user_id,))
        items = [{"id": r[0], "title": r[1], "body": r[2], "tags": [t for t in r[3].split(",") if t], "updated_at": r[4]} for r in rows]
        needle = search.strip().lower()
        return [i for i in items if not needle or needle in (i["title"] + " " + i["body"] + " " + " ".join(i["tags"])).lower()]

    def delete(self, user_id: str, prompt_id: str) -> None:
        self.db.execute("DELETE FROM workspace_prompts WHERE id=? AND user_id=?", (prompt_id, user_id))
        self.db.commit()

    def export_json(self, user_id: str) -> str:
        return json.dumps(self.list(user_id), indent=2)

    def export_markdown(self, user_id: str) -> str:
        parts = ["# My prompt workspace\n"]
        for item in self.list(user_id):
            tag_line = f"\n*Tags: {', '.join(item['tags'])}*\n" if item["tags"] else ""
            parts.append(f"## {item['title']}\n{tag_line}\n```\n{item['body']}\n```\n")
        return "\n".join(parts)
