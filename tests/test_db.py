"""Tests for database layer — schema bootstrap, upserts, queries."""
from __future__ import annotations

import json
import sqlite3

import pytest


# Patch DB_PATH before import so tests don't touch real DB
@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    db_file = tmp_path / "test_vyral.db"
    monkeypatch.setenv("VYRAL_DB_PATH", str(db_file))
    # Re-import config + db with new path
    import importlib

    import config
    importlib.reload(config)
    import database.db
    importlib.reload(database.db)
    yield db_file


def test_schema_creates_all_tables(isolated_db):
    from database.db import init_db
    init_db()
    conn = sqlite3.connect(isolated_db)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert {"posts", "sounds", "hooks", "timing_heatmap", "plans"} <= tables
    conn.close()


def test_upsert_post_inserts_and_updates(isolated_db, sample_post):
    from database.db import conn, init_db, upsert_post
    init_db()
    upsert_post(sample_post)
    with conn() as c:
        row = c.execute("SELECT id, like_count FROM posts WHERE id=?",
                        (sample_post["id"],)).fetchone()
        assert row["id"] == sample_post["id"]
        assert row["like_count"] == sample_post["like_count"]

    # Update via upsert
    updated = {**sample_post, "like_count": 99_999}
    upsert_post(updated)
    with conn() as c:
        row = c.execute("SELECT like_count FROM posts WHERE id=?",
                        (sample_post["id"],)).fetchone()
        assert row["like_count"] == 99_999


def test_upsert_post_serializes_hashtags(isolated_db, sample_post):
    from database.db import conn, init_db, upsert_post
    init_db()
    # snapshot the list before upsert (which serializes it in place)
    expected_hashtags = list(sample_post["hashtags"])
    upsert_post(sample_post)
    with conn() as c:
        row = c.execute("SELECT hashtags FROM posts WHERE id=?",
                        (sample_post["id"],)).fetchone()
        # hashtags column stored as JSON string
        loaded = json.loads(row["hashtags"])
        assert loaded == expected_hashtags


def test_top_posts_orders_by_viral_score(isolated_db, sample_post):
    from database.db import init_db, top_posts, upsert_post
    init_db()
    upsert_post({**sample_post, "id": "A", "viral_score": 50.0})
    upsert_post({**sample_post, "id": "B", "viral_score": 90.0})
    upsert_post({**sample_post, "id": "C", "viral_score": 10.0})

    results = top_posts(sample_post["niche"], limit=3)
    assert [r["id"] for r in results] == ["B", "A", "C"]
