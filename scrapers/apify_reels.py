"""Deep-dive on top reels via apify/instagram-reel-scraper — $1/1k.

This is the only actor returning transcripts + reliable audio_id.
Use sparingly: only on the top 5-10% from discovery (high viral_score).
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Iterable

from apify_client import ApifyClient

from config import APIFY_TOKEN, APIFY_ACTORS
from database import upsert_post, upsert_sound, conn


def _client() -> ApifyClient:
    if not APIFY_TOKEN:
        raise RuntimeError("APIFY_TOKEN missing in .env")
    return ApifyClient(APIFY_TOKEN)


def _parse_iso(ts: str | None) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except Exception:
        return ts


def deep_dive(post_ids_with_niche: list[tuple[str, str]]) -> int:
    """Pull transcripts + audio for given (shortcode, niche) pairs."""
    if not post_ids_with_niche:
        return 0
    client = _client()
    actor = client.actor(APIFY_ACTORS["reels"])
    urls = [f"https://www.instagram.com/reel/{pid}/" for pid, _ in post_ids_with_niche]
    niche_by_id = dict(post_ids_with_niche)

    inputs = {
        "username": urls,
        "resultsLimit": len(urls),
    }
    run = actor.call(run_input=inputs)
    count = 0
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        sc = item.get("shortCode") or item.get("id")
        if not sc:
            continue
        niche = niche_by_id.get(sc, "unknown")
        music = item.get("musicInfo") or {}
        audio_id = music.get("audio_id")

        row = {
            "id":              sc,
            "niche":           niche,
            "type":            "reel",
            "owner_username":  item.get("ownerUsername"),
            "owner_followers": item.get("ownerFollowersCount"),
            "caption":         item.get("caption"),
            "transcript":      item.get("transcript") or item.get("videoTranscript"),
            "audio_id":        audio_id,
            "audio_title":     music.get("song_name"),
            "audio_artist":    music.get("artist_name"),
            "posted_at":       _parse_iso(item.get("timestamp")),
            "play_count":      item.get("videoPlayCount") or item.get("playsCount"),
            "like_count":      item.get("likesCount"),
            "comment_count":   item.get("commentsCount"),
            "share_count":     item.get("reshareCount"),
            "view_count":      item.get("videoViewCount"),
            "hashtags":        item.get("hashtags") or [],
            "url":             item.get("url"),
            "video_duration":  item.get("videoDuration"),
            "viral_score":     None,
        }
        upsert_post(row)

        if audio_id:
            now = datetime.now(timezone.utc).isoformat()
            upsert_sound({
                "audio_id":          audio_id,
                "title":             music.get("song_name"),
                "artist":            music.get("artist_name"),
                "first_seen":        now,
                "last_seen":         now,
                "usage_count":       1,
                "avg_play_count":    row["play_count"] or 0,
                "lifecycle":         "rising",
                "source":            "instagram",
                "tiktok_first_seen": None,
            })
        count += 1
    return count


def top_candidates_for_deepdive(niche: str, limit: int = 50) -> list[tuple[str, str]]:
    """Pick top reels with NULL transcript = deep-dive candidates."""
    with conn() as c:
        rows = c.execute(
            "SELECT id FROM posts WHERE niche=? AND type='reel' AND transcript IS NULL "
            "ORDER BY COALESCE(play_count, like_count*30, 0) DESC LIMIT ?",
            (niche, limit),
        ).fetchall()
        return [(r["id"], niche) for r in rows]


if __name__ == "__main__":
    from config import NICHES
    for n in NICHES:
        cands = top_candidates_for_deepdive(n, limit=20)
        print(f"[deepdive] niche={n} candidates={len(cands)}")
        if cands:
            c = deep_dive(cands)
            print(f"  enriched {c} reels")
