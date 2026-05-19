"""7-day viral post plan generator.

Combines:
  - top hook formulas (from analyzer/hooks.py)
  - best rising sounds (from analyzer/sounds.py)
  - best posting slots (from analyzer/timing.py)
  - Claude API for concept + caption generation
  - compliance filtering (ban words, caption length, hashtags)

Output: JSON plan stored in `plans` table, returned as dict.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

from analyzer.hooks import top_hooks
from analyzer.sounds import best_sounds_for_planner
from analyzer.timing import DAY_NAMES, best_slots
from config import NICHES
from database import conn
from planner.llm_brain import generate_post_concept


def _validate_compliance(post: dict, niche: str) -> tuple[bool, list[str]]:
    cfg = NICHES[niche]["compliance"]
    issues = []
    caption = (post.get("caption") or "").lower()

    if len(post.get("caption", "")) > cfg["max_caption_chars"]:
        issues.append(f"caption > {cfg['max_caption_chars']} chars")

    for word in cfg["ban_words_caption"]:
        if word.lower() in caption:
            issues.append(f"banned word: {word}")

    hashtags = post.get("hashtags", [])
    if len(hashtags) > cfg["max_hashtags"]:
        issues.append(f"too many hashtags ({len(hashtags)} > {cfg['max_hashtags']})")

    return (len(issues) == 0, issues)


def generate_week(niche: str, week_start: date, theme: str = "general growth") -> dict:
    """Generate 7-day plan. Stores in DB. Returns full plan dict."""
    if niche not in NICHES:
        raise ValueError(f"unknown niche: {niche}")

    hooks = top_hooks(niche, limit=10)
    if not hooks:
        raise RuntimeError(f"no hooks for niche={niche} — run analyzer/hooks.py first")

    sounds = best_sounds_for_planner(limit=10)
    slots = best_slots(niche, n=7)

    if not slots:
        # Fallback: default best times if heatmap empty
        slots = [
            {"day_of_week": d, "hour_of_day": h, "avg_score": 0, "sample_size": 0}
            for d, h in [(1, 19), (2, 19), (3, 21), (4, 19), (5, 12), (6, 11), (0, 18)]
        ]

    plan_posts = []
    for i, slot in enumerate(slots):
        hook = hooks[i % len(hooks)]
        sound = sounds[i % len(sounds)] if sounds else {"title": None, "artist": None, "audio_id": None}
        slot_date = week_start + timedelta(days=(slot["day_of_week"] - week_start.weekday()) % 7)

        concept = generate_post_concept(
            niche=niche,
            theme=theme,
            hook_formula=hook["formula"],
            hook_example=hook.get("example", ""),
            sound_title=sound.get("title"),
            sound_artist=sound.get("artist"),
            day_label=DAY_NAMES[slot["day_of_week"]],
            hour=slot["hour_of_day"],
        )

        ok, issues = _validate_compliance(concept, niche)

        plan_posts.append({
            "day_of_week":    DAY_NAMES[slot["day_of_week"]],
            "date":           slot_date.isoformat(),
            "hour":           slot["hour_of_day"],
            "timing_score":   slot.get("avg_score"),
            "hook_formula":   hook["formula"],
            "hook_example":   hook.get("example"),
            "sound": {
                "audio_id": sound.get("audio_id"),
                "title":    sound.get("title"),
                "artist":   sound.get("artist"),
                "lifecycle": sound.get("lifecycle"),
            },
            "concept":        concept,
            "compliance_ok":  ok,
            "compliance_issues": issues,
        })

    plan = {
        "niche":      niche,
        "week_start": week_start.isoformat(),
        "theme":      theme,
        "posts":      plan_posts,
    }

    with conn() as c:
        c.execute(
            "INSERT INTO plans (niche, week_start, theme, plan_json) VALUES (?, ?, ?, ?)",
            (niche, week_start.isoformat(), theme, json.dumps(plan, ensure_ascii=False)),
        )
    return plan


if __name__ == "__main__":
    import sys
    niche = sys.argv[1] if len(sys.argv) > 1 else "fashion-lifestyle"
    theme = sys.argv[2] if len(sys.argv) > 2 else "summer vibes"
    monday = date.today() - timedelta(days=date.today().weekday())
    next_monday = monday + timedelta(days=7)
    plan = generate_week(niche, next_monday, theme)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
