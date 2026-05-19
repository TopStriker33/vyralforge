"""Shared pytest fixtures."""
from __future__ import annotations
import sys
from pathlib import Path

# Add project root to sys.path so tests can `from config import ...`
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest


@pytest.fixture
def sample_post() -> dict:
    """One realistic post dict for scoring/analysis tests."""
    return {
        "id":              "ABC123",
        "niche":           "fashion-lifestyle",
        "type":            "reel",
        "owner_username":  "test_user",
        "owner_followers": 10_000,
        "caption":         "test caption with #ootd",
        "transcript":      "hey everyone today I want to show you",
        "audio_id":        "audio_001",
        "audio_title":     "Test Track",
        "audio_artist":    "Test Artist",
        "posted_at":       "2026-05-19T14:30:00+00:00",
        "play_count":      50_000,
        "like_count":      3_500,
        "comment_count":   120,
        "share_count":     None,
        "view_count":      None,
        "hashtags":        ["ootd", "fashion", "style"],
        "url":             "https://www.instagram.com/reel/ABC123/",
        "video_duration":  12.5,
        "viral_score":     None,
    }


@pytest.fixture
def low_perf_post(sample_post: dict) -> dict:
    """Same shape but low engagement."""
    return {**sample_post, "id": "LOW123",
            "play_count": 800, "like_count": 30, "comment_count": 2}


@pytest.fixture
def high_perf_post(sample_post: dict) -> dict:
    """Same shape but viral."""
    return {**sample_post, "id": "HIGH123",
            "play_count": 2_000_000, "like_count": 150_000, "comment_count": 8_500,
            "share_count": 12_000}
