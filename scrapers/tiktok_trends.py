"""TikTok sound trend radar — J-3 first-mover advantage.

Sounds that explode on TikTok hit Instagram Reels 48-72h later.
This module pulls TikTok trending sounds and stores them so the planner
can pick rising sounds BEFORE they saturate Reels.

Uses davidteather/TikTok-Api (OSS). Needs `ms_token` from a logged-in
browser session (cookie) — see README. Falls back gracefully if unavailable.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from config import TIKTOK_MS_TOKEN
from database import upsert_sound


async def _fetch_trending_sounds(count: int = 50) -> list[dict]:
    """Pull TikTok trending sounds via TikTokApi. Returns raw items."""
    try:
        from TikTokApi import TikTokApi
    except ImportError:
        print("TikTokApi not installed — run: pip install TikTokApi && playwright install")
        return []
    if not TIKTOK_MS_TOKEN:
        print("TIKTOK_MS_TOKEN missing — see README for cookie extraction")
        return []

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[TIKTOK_MS_TOKEN],
            num_sessions=1,
            sleep_after=3,
        )
        items = []
        async for video in api.trending.videos(count=count):
            d = video.as_dict
            music = d.get("music") or {}
            items.append({
                "audio_id": str(music.get("id")) if music.get("id") else None,
                "title":    music.get("title"),
                "artist":   music.get("authorName"),
                "play_count": (d.get("stats") or {}).get("playCount", 0),
            })
        return items


def pull_tiktok_trends(count: int = 50) -> int:
    """Sync wrapper. Returns count of sounds stored."""
    items = asyncio.run(_fetch_trending_sounds(count))
    now = datetime.now(timezone.utc).isoformat()
    stored = 0
    for it in items:
        if not it["audio_id"]:
            continue
        upsert_sound({
            "audio_id":          it["audio_id"],
            "title":             it["title"],
            "artist":            it["artist"],
            "first_seen":        now,
            "last_seen":         now,
            "usage_count":       1,
            "avg_play_count":    it["play_count"],
            "lifecycle":         "rising",
            "source":            "tiktok",
            "tiktok_first_seen": now,
        })
        stored += 1
    return stored


if __name__ == "__main__":
    n = pull_tiktok_trends(50)
    print(f"[tiktok-radar] stored {n} rising sounds")
