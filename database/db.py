"""SQLite helper — connection, schema bootstrap, basic queries."""
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator, Any

from config import DB_PATH

SCHEMA_FILE = Path(__file__).parent / "schema.sql"


@contextmanager
def conn() -> Iterator[sqlite3.Connection]:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON;")
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db() -> None:
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    with conn() as c:
        c.executescript(schema)


def upsert_post(row: dict[str, Any]) -> None:
    if isinstance(row.get("hashtags"), list):
        row["hashtags"] = json.dumps(row["hashtags"])
    cols = ", ".join(row.keys())
    placeholders = ", ".join(f":{k}" for k in row)
    updates = ", ".join(f"{k}=excluded.{k}" for k in row if k != "id")
    sql = (
        f"INSERT INTO posts ({cols}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}"
    )
    with conn() as c:
        c.execute(sql, row)


def upsert_sound(row: dict[str, Any]) -> None:
    cols = ", ".join(row.keys())
    placeholders = ", ".join(f":{k}" for k in row)
    updates = ", ".join(f"{k}=excluded.{k}" for k in row if k != "audio_id")
    sql = (
        f"INSERT INTO sounds ({cols}) VALUES ({placeholders}) "
        f"ON CONFLICT(audio_id) DO UPDATE SET {updates}"
    )
    with conn() as c:
        c.execute(sql, row)


def top_posts(niche: str, limit: int = 50) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM posts WHERE niche = ? ORDER BY viral_score DESC LIMIT ?",
            (niche, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def rising_sounds(limit: int = 20) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM sounds WHERE lifecycle IN ('rising','peak') "
            "ORDER BY usage_count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
