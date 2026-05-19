"""Claude prompts for generating viral post concepts + captions.

Keeps prompt engineering separate from orchestration logic.
"""
from __future__ import annotations
import json
import re

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, NICHES


def _client() -> Anthropic:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY missing in .env")
    return Anthropic(api_key=ANTHROPIC_API_KEY)


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()


def generate_post_concept(
    niche: str,
    theme: str,
    hook_formula: str,
    hook_example: str,
    sound_title: str | None,
    sound_artist: str | None,
    day_label: str,
    hour: int,
) -> dict:
    """One post concept: visual idea + caption + hashtags. Returns dict."""
    cfg = NICHES[niche]
    comp = cfg["compliance"]
    ban_words = ", ".join(comp["ban_words_caption"])
    ctas = " | ".join(comp["preferred_cta"])

    sound_line = (
        f'TRENDING SOUND TO USE: "{sound_title}" by {sound_artist}'
        if sound_title else "TRENDING SOUND: none (use original audio or popular evergreen)"
    )

    prompt = f"""You are a senior creator-economy growth strategist. Generate ONE viral Instagram Reel concept.

NICHE: {cfg['label']}
ANGLE: {cfg['angle']}
WEEKLY THEME: {theme}
SLOT: {day_label} {hour:02d}h00 (local time)

HOOK FORMULA TO USE: {hook_formula}
HOOK EXAMPLE (do NOT copy, use as style ref): "{hook_example}"

{sound_line}

CONSTRAINTS (hard rules — break = post killed):
- Caption ≤ {comp['max_caption_chars']} chars (before "...more" cutoff)
- Max {comp['max_hashtags']} hashtags, niche-specific only
- BANNED words in caption: {ban_words}
- Use ONE of these CTA styles: {ctas}
- No TikTok/CapCut watermarks (re-export clean)
- Pattern interrupt in first 0.5s (sudden zoom, color shift, text appearing)
- 3-second hold rate is the kill metric

Return STRICT JSON:
{{
  "visual_concept": "1-2 sentence shoot description (what camera sees, what creator does)",
  "first_frame": "exact description of frame 0 — must stop the scroll",
  "first_3s_action": "what happens in 0-3s to lock the watch",
  "caption": "the actual caption text, ≤{comp['max_caption_chars']} chars",
  "hashtags": ["hashtag1", "hashtag2", ...],
  "cta_type": "Comment X | DM keyword | Bio link | Save",
  "expected_dm_trigger": "what will make people share this in DMs (the #1 algo signal)"
}}

JSON only, no prose."""

    msg = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    text = _strip_fences(msg.content[0].text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_raw": text, "_error": "json_parse_failed"}
