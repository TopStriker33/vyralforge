"""Hook extraction — finds the top 10 hook formulas per niche.

Takes the top N viral posts, extracts caption + transcript first line,
feeds to Claude API to classify into known formulas (POV, transformation,
forbidden knowledge, etc.) or discover new ones. Stores in `hooks` table.
"""
from __future__ import annotations
import json
import re
from typing import Any

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, NICHES
from database import conn

KNOWN_FORMULAS = [
    "POV first-person",
    "Transformation timeline",
    "Forbidden knowledge",
    "Identity callout",
    "Curiosity gap",
    "Direct command",
    "Hot take",
    "X for 30 days",
    "Reveal-first",
    "Specificity number",
]


def _first_lines(post: dict) -> str:
    caption = (post.get("caption") or "").strip()
    transcript = (post.get("transcript") or "").strip()
    cap_first = caption.split("\n")[0][:200] if caption else ""
    trans_first = " ".join(transcript.split()[:30]) if transcript else ""
    return f"CAPTION: {cap_first}\nTRANSCRIPT_FIRST_3S: {trans_first}"


def extract_hooks(niche: str, top_n: int = 30) -> int:
    """Pick top_n posts by viral_score, classify hooks via Claude. Returns stored count."""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY missing in .env")

    with conn() as c:
        rows = [dict(r) for r in c.execute(
            "SELECT id, caption, transcript, viral_score FROM posts "
            "WHERE niche=? AND viral_score IS NOT NULL "
            "ORDER BY viral_score DESC LIMIT ?",
            (niche, top_n),
        ).fetchall()]

    if not rows:
        return 0

    samples = "\n\n---\n\n".join(
        f"[POST {i+1}] (score={r['viral_score']})\n{_first_lines(r)}"
        for i, r in enumerate(rows)
    )

    formulas_str = ", ".join(KNOWN_FORMULAS)
    prompt = f"""You analyze viral Instagram Reels for the niche: {NICHES[niche]['label']}.

Below are the top {len(rows)} performing posts. For EACH post, classify the hook into ONE of these known formulas (or propose a new one if none fit):

{formulas_str}

Return STRICT JSON array, one object per post:
[
  {{"post_index": 1, "formula": "POV first-person", "extracted_hook": "POV: you matched with the girl your friends warned you about", "why_it_works": "first-person tension + social proof"}},
  ...
]

POSTS:
{samples}

JSON only, no prose."""

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    # strip code fences if present
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()

    try:
        classifications = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[hooks] JSON parse failed: {e}\n--- raw ---\n{text[:500]}")
        return 0

    stored = 0
    with conn() as c:
        c.execute("DELETE FROM hooks WHERE niche=?", (niche,))
        for cls in classifications:
            idx = cls.get("post_index", 0) - 1
            if not (0 <= idx < len(rows)):
                continue
            post = rows[idx]
            c.execute(
                "INSERT INTO hooks (niche, formula, example, avg_score, sample_post_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    niche,
                    cls.get("formula", "unknown"),
                    cls.get("extracted_hook", ""),
                    post["viral_score"],
                    post["id"],
                ),
            )
            stored += 1
    return stored


def top_hooks(niche: str, limit: int = 10) -> list[dict]:
    """Return top hooks by formula, ranked by avg_score across samples."""
    with conn() as c:
        rows = c.execute(
            "SELECT formula, AVG(avg_score) as score, COUNT(*) as n, "
            "MAX(example) as example "
            "FROM hooks WHERE niche=? "
            "GROUP BY formula ORDER BY score DESC LIMIT ?",
            (niche, limit),
        ).fetchall()
        return [dict(r) for r in rows]


if __name__ == "__main__":
    for n in NICHES:
        c = extract_hooks(n, top_n=30)
        print(f"[hooks] niche={n} classified={c}")
        for h in top_hooks(n, 5):
            print(f"  - {h['formula']}: {h['example'][:80]}  (avg {h['score']:.1f}, n={h['n']})")
