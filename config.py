"""Vyral Forge config — niches, thresholds, compliance rules.

This is the example config. Customize NICHES, SCORE_WEIGHTS, and compliance
rules to fit your specific creator vertical. The library treats niches as
opaque tags — pick whatever names make sense for your work.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

ROOT = Path(__file__).parent
DB_PATH = Path(os.getenv("VYRAL_DB_PATH", ROOT / "data" / "vyral.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TIKTOK_MS_TOKEN = os.getenv("TIKTOK_MS_TOKEN", "")

# Apify actor IDs (validated against Apify Store, May 2026)
APIFY_ACTORS = {
    "discover": "apidojo/instagram-scraper",       # ~$0.50/1k posts
    "reels":    "apify/instagram-reel-scraper",    # ~$1.00/1k, has transcripts + audio_id
    "profile":  "apify/instagram-profile-scraper", # ~$1.60/1k
}

# Niches — these are EXAMPLE presets. Replace with your verticals.
# Each niche = hashtag seeds + seed accounts + content angle + compliance rules.
NICHES = {
    "fashion-lifestyle": {
        "label": "Fashion & lifestyle creator",
        "hashtags": [
            "ootd", "fashioninspo", "outfitideas", "styleinspo",
            "fashionblogger", "lifestylevlog", "dayinmylife", "grwm",
        ],
        "seed_accounts": [],
        "angle": "shareable lifestyle content → newsletter / shop funnel",
        "compliance": {
            "ban_words_caption": ["link in bio", "subscribe", "buy now"],
            "preferred_cta": ["Comment STYLE", "DM me 'fit'", "Save for later"],
            "max_caption_chars": 220,
            "max_hashtags": 5,
        },
    },
    "fitness-wellness": {
        "label": "Fitness & wellness creator",
        "hashtags": [
            "fitnessmotivation", "gymgirl", "fitfam", "workoutvideo",
            "wellnessjourney", "healthyliving", "morningroutine", "fittok",
        ],
        "seed_accounts": [],
        "angle": "algorithm-friendly reach → bio link → newsletter / coaching",
        "compliance": {
            "ban_words_caption": ["link in bio", "subscribe"],
            "preferred_cta": ["Full vlog on my page", "Link in bio", "Comment FIT"],
            "max_caption_chars": 220,
            "max_hashtags": 5,
        },
    },
}

# Viral score weights — derived from public 2026 Instagram algorithm research.
# Adjust based on your niche's actual signal weights.
SCORE_WEIGHTS = {
    "dm_sends_per_reach":   0.30,  # #1 signal in 2026 per Adam Mosseri (head of Instagram)
    "watch_time_seconds":   0.20,
    "saves_per_reach":      0.15,
    "hold_rate_3s":         0.15,
    "completion_rate":      0.10,
    "comment_depth":        0.05,
    "profile_clicks":       0.03,
    "likes_per_reach":      0.02,
}

# Sound trend lifecycle (days since first detection)
SOUND_LIFECYCLE = {
    "rising":   (0, 3),    # use NOW (cross-platform first-mover window)
    "peak":     (3, 7),    # still effective
    "dying":    (7, 14),   # avoid for new posts
    "dead":     (14, 999), # do not use
}

# Pattern triggers that the planner blocks before posting.
# Add your platform-specific anti-flag rules here.
DISTRIBUTION_TRIGGERS = [
    "tiktok_watermark", "capcut_watermark",
    "direct_external_link_pattern", "mass_dm_velocity", "mass_follow_velocity",
]
