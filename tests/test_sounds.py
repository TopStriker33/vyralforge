"""Tests for analyzer/sounds.py lifecycle classification."""
from __future__ import annotations

from analyzer.sounds import _classify_age, _parse


def test_classify_age_rising():
    assert _classify_age(0.5) == "rising"
    assert _classify_age(2.9) == "rising"


def test_classify_age_peak():
    assert _classify_age(3.0) == "peak"
    assert _classify_age(6.5) == "peak"


def test_classify_age_dying():
    assert _classify_age(7.0) == "dying"
    assert _classify_age(13.9) == "dying"


def test_classify_age_dead():
    assert _classify_age(14.0) == "dead"
    assert _classify_age(999.9) == "dead"


def test_parse_handles_z_suffix():
    dt = _parse("2026-05-19T14:30:00Z")
    assert dt is not None
    assert dt.tzinfo is not None


def test_parse_handles_offset_format():
    dt = _parse("2026-05-19T14:30:00+00:00")
    assert dt is not None


def test_parse_handles_none():
    assert _parse(None) is None


def test_parse_handles_garbage():
    assert _parse("not a date") is None
