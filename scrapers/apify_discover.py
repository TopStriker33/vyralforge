"""Bulk discovery via apidojo/instagram-scraper — $0.50/1k posts.

Pulls top posts/reels per niche hashtag set. Cheap, no transcripts.
Use to build the candidate pool. Deep-dive only the top 5-10% later.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Iterable

from apify_client import ApifyClient

from config import APIFY_TOKEN, APIFY_ACTORS, NICHES
from database import upsert_post


def _client() -> ApifyClient:
    if not APIFY_TOKEN:
        raise RuntimeError("APIFY_TOKEN missing in .env — sign up at apify.com ($5 free credit)")
    return ApifyClient(APIFY_TOKEN)


def _parse_iso(ts: str | None) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except Exception:
        return ts


def _map(item: dict, niche: str) -> dict:
    """Normalize apidojo output to our posts schema."""
    return {
        "id":              item.get("shortCode") or item.get("id"),
        "niche":           niche,
        "type":            (item.get("type") or "post").lower(),
        "owner_username":  item.get("ownerUsername"),
        "owner_followers": item.get("ownerFollowersCount"),
        "caption":         item.get("caption"),
        "transcript":      None,
        "audio_id":        (item.get("musicInfo") or {}).get("audio_id"),
        "audio_title":     (item.get("musicInfo") or {}).get("song_name"),
        "audio_artist":    (item.get("musicInfo") or {}).get("artist_name"),
        "posted_at":       _parse_iso(item.get("timestamp")),
        "play_count":      item.get("videoPlayCount") or item.get("playsCount"),
        "like_count":      item.get("likesCount"),
        "comment_count":   item.get("commentsCount"),
        "share_count":     None,
        "view_count":      item.get("videoViewCount"),
        "hashtags":        item.get("hashtags") or [],
        "url":             item.get("url"),
        "video_duration":  item.get("videoDuration"),
        "viral_score":     None,
    }


def discover_by_hashtags(niche: str, results_per_tag: int = 50) -> int:
    """Run apidojo scraper for each hashtag of a niche. Returns count ingested."""
    cfg = NICHES[niche]
    client = _client()
    actor = client.actor(APIFY_ACTORS["discover"])

    inputs = {
        "search": [f"#{t}" for t in cfg["hashtags"]],
        "searchType": "hashtag",
        "resultsType": "posts",
        "resultsLimit": results_per_tag,
        "addParentData": False,
    }
    run = actor.call(run_input=inputs)
    count = 0
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        row = _map(item, niche)
        if not row["id"]:
            continue
        upsert_post(row)
        count += 1
    return count


def discover_by_accounts(niche: str, usernames: Iterable[str], results_per_account: int = 30) -> int:
    cfg_actor = APIFY_ACTORS["discover"]
    client = _client()
    actor = client.actor(cfg_actor)
    inputs = {
        "directUrls": [f"https://www.instagram.com/{u}/" for u in usernames],
        "resultsType": "posts",
        "resultsLimit": results_per_account,
    }
    run = actor.call(run_input=inputs)
    count = 0
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        row = _map(item, niche)
        if not row["id"]:
            continue
        upsert_post(row)
        count += 1
    return count


if __name__ == "__main__":
    from database import init_db
    init_db()
    for n in NICHES:
        print(f"[discover] niche={n} ...")
        c = discover_by_hashtags(n, results_per_tag=30)
        print(f"  ingested {c} posts")
