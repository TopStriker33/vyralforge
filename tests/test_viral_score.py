"""Tests for analyzer/viral_score._raw_score scoring logic."""
from __future__ import annotations

from analyzer.viral_score import _raw_score, _safe


class TestSafe:
    def test_none_returns_default(self):
        assert _safe(None) == 0.0
        assert _safe(None, default=42.0) == 42.0

    def test_int_returns_float(self):
        assert _safe(5) == 5.0
        assert isinstance(_safe(5), float)

    def test_string_int_returns_float(self):
        assert _safe("10") == 10.0

    def test_garbage_returns_default(self):
        assert _safe("not a number", default=1.0) == 1.0
        assert _safe({}, default=2.0) == 2.0


class TestRawScore:
    def test_high_perf_scores_above_low_perf(self, low_perf_post, high_perf_post):
        assert _raw_score(high_perf_post) > _raw_score(low_perf_post)

    def test_zero_engagement_does_not_crash(self):
        post = {
            "play_count": 0, "like_count": 0, "comment_count": 0,
            "share_count": 0, "video_duration": 0, "owner_followers": 0,
        }
        score = _raw_score(post)
        assert isinstance(score, float)
        assert score >= 0.0

    def test_score_is_nonneg(self, sample_post):
        assert _raw_score(sample_post) >= 0.0

    def test_missing_keys_handled(self):
        post = {"play_count": 1000, "like_count": 50}
        score = _raw_score(post)
        assert isinstance(score, float)
