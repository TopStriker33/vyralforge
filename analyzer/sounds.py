"""Sound lifecycle classifier — rising / peak / dying / dead.

Combines: time since first_seen + usage growth + TikTok lead time.
Rule of thumb: sounds peak 3-7 days post-detection, die by day 14.
TikTok-first sounds get a "rising" boost for 72h after IG appearance.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta

from config import SOUND_LIFECYCLE
from database import conn


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _classify_age(days: float) -> str:
    for label, (lo, hi) in SOUND_LIFECYCLE.items():
        if lo <= days < hi:
            return label
    return "dead"


def refresh_lifecycle() -> int:
    """Re-classify every sound based on age + usage."""
    now = datetime.now(timezone.utc)
    updated = 0
    with conn() as c:
        rows = c.execute("SELECT * FROM sounds").fetchall()
        for r in rows:
            first = _parse(r["first_seen"]) or now
            age_days = (now - first).total_seconds() / 86400
            label = _classify_age(age_days)

            # TikTok-first boost: if seen on TT before IG, stay "rising" longer
            tt_first = _parse(r["tiktok_first_seen"])
            if tt_first and (now - tt_first).total_seconds() < 72 * 3600:
                label = "rising"

            # Recount usage from posts table
            usage = c.execute(
                "SELECT COUNT(*) as n, AVG(play_count) as avg_p FROM posts WHERE audio_id=?",
                (r["audio_id"],),
            ).fetchone()

            c.execute(
                "UPDATE sounds SET lifecycle=?, usage_count=?, avg_play_count=?, last_seen=? "
                "WHERE audio_id=?",
                (
                    label,
                    usage["n"] or r["usage_count"],
                    usage["avg_p"] or r["avg_play_count"],
                    now.isoformat(),
                    r["audio_id"],
                ),
            )
            updated += 1
    return updated


def best_sounds_for_planner(limit: int = 7) -> list[dict]:
    """Top rising/peak sounds with usage > 1 (validated)."""
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM sounds WHERE lifecycle IN ('rising','peak') "
            "AND usage_count >= 1 "
            "ORDER BY CASE lifecycle WHEN 'rising' THEN 0 ELSE 1 END, "
            "usage_count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


if __name__ == "__main__":
    n = refresh_lifecycle()
    print(f"[sounds] refreshed lifecycle on {n} sounds")
    for s in best_sounds_for_planner(10):
        print(f"  - [{s['lifecycle']}] {s['title']} by {s['artist']}  (used {s['usage_count']}x)")
