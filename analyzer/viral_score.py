"""Viral score — predicts post performance from 2026 algo signals.

Weights from intel: DM-sends-per-reach (#1) > watch_time > saves > 3-sec hold.
Since save_count + share_count are often NULL on Apify, we use proxies:
  - DM sends ≈ (comments + saves) per follower
  - watch_time ≈ play_count × video_duration (rough)
  - 3-sec hold ≈ play_count / unique_reach (proxy)

Output: 0-100 score, normalized within niche.
"""
from __future__ import annotations
import math
import statistics

from config import SCORE_WEIGHTS, NICHES
from database import conn


def _safe(v, default=0.0):
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _raw_score(row: dict) -> float:
    plays     = _safe(row.get("play_count"))
    likes     = _safe(row.get("like_count"))
    comments  = _safe(row.get("comment_count"))
    shares    = _safe(row.get("share_count"))
    duration  = _safe(row.get("video_duration"), 15.0) or 15.0
    followers = _safe(row.get("owner_followers"), 1000.0) or 1000.0

    reach_proxy = max(plays, likes * 8, 1.0)

    dm_sends_proxy   = (comments + shares) / reach_proxy
    watch_time_proxy = (plays * duration) / max(followers, 1.0)
    saves_proxy      = comments / max(reach_proxy, 1.0)
    hold_3s_proxy    = min(plays / max(followers, 1.0), 1.0)
    completion_proxy = min((duration / 30.0), 1.0)
    comment_depth    = math.log1p(comments) / 10.0
    profile_clicks   = comments / max(followers, 1.0)
    likes_per_reach  = likes / max(reach_proxy, 1.0)

    raw = (
        SCORE_WEIGHTS["dm_sends_per_reach"]   * dm_sends_proxy   * 100
        + SCORE_WEIGHTS["watch_time_seconds"] * watch_time_proxy * 10
        + SCORE_WEIGHTS["saves_per_reach"]    * saves_proxy      * 100
        + SCORE_WEIGHTS["hold_rate_3s"]       * hold_3s_proxy    * 100
        + SCORE_WEIGHTS["completion_rate"]    * completion_proxy * 100
        + SCORE_WEIGHTS["comment_depth"]      * comment_depth    * 100
        + SCORE_WEIGHTS["profile_clicks"]     * profile_clicks   * 1000
        + SCORE_WEIGHTS["likes_per_reach"]    * likes_per_reach  * 100
    )
    return raw


def score_all_posts() -> int:
    """Compute and persist viral_score for every post. Normalized per-niche to 0-100."""
    updated = 0
    for niche in NICHES:
        with conn() as c:
            rows = [dict(r) for r in c.execute(
                "SELECT * FROM posts WHERE niche=?", (niche,)
            ).fetchall()]
            if not rows:
                continue

            raw_scores = {r["id"]: _raw_score(r) for r in rows}
            vals = list(raw_scores.values())
            if not vals or max(vals) == 0:
                continue

            # robust normalization: clip at 95th percentile to avoid outliers crushing the scale
            sorted_vals = sorted(vals)
            p95 = sorted_vals[int(len(sorted_vals) * 0.95)] if len(sorted_vals) > 5 else max(vals)
            denom = max(p95, 1e-6)

            for pid, raw in raw_scores.items():
                norm = min(100.0, (raw / denom) * 100)
                c.execute(
                    "UPDATE posts SET viral_score=? WHERE id=?",
                    (round(norm, 2), pid),
                )
                updated += 1
    return updated


if __name__ == "__main__":
    n = score_all_posts()
    print(f"[viral-score] scored {n} posts")
