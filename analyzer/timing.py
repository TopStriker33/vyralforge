"""Posting timing heatmap — best day×hour per niche, weighted by viral_score.

Algorithm:
  1. Bucket all scored posts by (day_of_week, hour_of_day) in user's local TZ.
  2. Weighted avg viral_score per bucket.
  3. Rolling-sum smoothing across adjacent hours (Sandreke-inspired).
  4. Persist to timing_heatmap table.
  5. Planner picks top 7 distinct (day,hour) slots for the week.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import NICHES
from database import conn

LOCAL_TZ = ZoneInfo("Europe/Zurich")  # Ethan's home TZ (Bern principal)


def _to_local(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(LOCAL_TZ)
    except Exception:
        return None


def build_heatmap() -> int:
    """Compute and persist heatmap. Returns row count."""
    with conn() as c:
        c.execute("DELETE FROM timing_heatmap")
        total_rows = 0
        for niche in NICHES:
            posts = c.execute(
                "SELECT posted_at, viral_score FROM posts "
                "WHERE niche=? AND viral_score IS NOT NULL AND posted_at IS NOT NULL",
                (niche,),
            ).fetchall()

            buckets = defaultdict(list)
            for p in posts:
                dt = _to_local(p["posted_at"])
                if not dt:
                    continue
                buckets[(dt.weekday(), dt.hour)].append(p["viral_score"])

            # Raw averages
            raw = {k: (sum(v) / len(v), len(v)) for k, v in buckets.items()}

            # Smooth ±1 hour (rolling sum)
            smoothed = {}
            for (d, h), (avg, n) in raw.items():
                neighbors = [
                    raw.get((d, (h + dh) % 24)) for dh in (-1, 0, 1)
                ]
                vals = [x[0] for x in neighbors if x]
                weights = [x[1] for x in neighbors if x]
                sm_avg = sum(v * w for v, w in zip(vals, weights)) / max(sum(weights), 1)
                smoothed[(d, h)] = (sm_avg, n)

            for (d, h), (avg, n) in smoothed.items():
                c.execute(
                    "INSERT INTO timing_heatmap (niche, day_of_week, hour_of_day, sample_size, avg_score) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (niche, d, h, n, round(avg, 2)),
                )
                total_rows += 1
        return total_rows


def best_slots(niche: str, n: int = 7) -> list[dict]:
    """Top-N distinct (day, hour) slots for the niche, ensuring spread across week."""
    with conn() as c:
        rows = c.execute(
            "SELECT day_of_week, hour_of_day, avg_score, sample_size FROM timing_heatmap "
            "WHERE niche=? AND sample_size >= 2 "
            "ORDER BY avg_score DESC",
            (niche,),
        ).fetchall()

    seen_days = set()
    picks = []
    for r in rows:
        d = r["day_of_week"]
        if d in seen_days:
            continue
        picks.append(dict(r))
        seen_days.add(d)
        if len(picks) >= n:
            break

    # If <7 distinct days, fill with next-best regardless
    if len(picks) < n:
        for r in rows:
            if len(picks) >= n:
                break
            row = dict(r)
            if row not in picks:
                picks.append(row)
    return picks[:n]


DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


if __name__ == "__main__":
    n = build_heatmap()
    print(f"[timing] heatmap rows={n}")
    for niche in NICHES:
        print(f"\n  niche={niche}")
        for s in best_slots(niche, 7):
            print(f"    {DAY_NAMES[s['day_of_week']]} {s['hour_of_day']:02d}h  "
                  f"(score {s['avg_score']:.1f}, n={s['sample_size']})")
