import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import Note


class NoteStorage:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_dir = Path.home() / ".qnote"
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "notes.db"
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    content  TEXT NOT NULL,
                    tags     TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_note(self, note: Note) -> Note:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (content, tags, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (note.content, note.tags_str(), now, now),
            )
            conn.commit()
        note.id = cursor.lastrowid
        note.created_at = datetime.fromisoformat(now)
        note.updated_at = datetime.fromisoformat(now)
        return note

    def get_note(self, note_id: int) -> Optional[Note]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, content, tags, created_at, updated_at FROM notes WHERE id = ?",
                (note_id,),
            ).fetchone()
        return Note.from_row(row) if row else None

    def list_notes(self, tag: Optional[str] = None, limit: int = 20) -> List[Note]:
        with self._connect() as conn:
            if tag:
                rows = conn.execute(
                    """SELECT id, content, tags, created_at, updated_at FROM notes
                       WHERE tags LIKE ? ORDER BY id DESC LIMIT ?""",
                    (f"%{tag}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, content, tags, created_at, updated_at FROM notes ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [Note.from_row(r) for r in rows]

    def search_notes(self, query: str) -> List[Note]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, content, tags, created_at, updated_at FROM notes
                   WHERE content LIKE ? ORDER BY id DESC""",
                (f"%{query}%",),
            ).fetchall()
        return [Note.from_row(r) for r in rows]

    def delete_note(self, note_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
        return cursor.rowcount > 0

    def get_all_tags(self) -> List[tuple]:
        with self._connect() as conn:
            rows = conn.execute("SELECT tags FROM notes WHERE tags != ''").fetchall()
        counts: dict = {}
        for (tags_str,) in rows:
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    counts[tag] = counts.get(tag, 0) + 1
        return sorted(counts.items(), key=lambda x: -x[1])

    def export_all(self) -> List[Note]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, content, tags, created_at, updated_at FROM notes ORDER BY id"
            ).fetchall()
        return [Note.from_row(r) for r in rows]
