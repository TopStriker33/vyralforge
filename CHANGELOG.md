# Changelog

All notable changes to Vyral Forge are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Phase 2: Multi-account scheduler (Metricool/Meta Graph API integration)
- Phase 3: Native TikTok Business API analytics
- Phase 4: AI gen pipeline (ComfyUI/Flux LoRA integration)
- Phase 5: X (Twitter) virality engine port
- Phase 6: Multi-creator collaboration layer (VA permissions)

## [0.1.0] — 2026-05-19

### Added
- Initial public release
- Apify-based bulk Instagram discovery (`apidojo/instagram-scraper`)
- Apify reel deep-dive with transcripts and audio_id (`apify/instagram-reel-scraper`)
- TikTok-Api cross-platform sound trend radar (48-72h ahead of Reels adoption)
- 2026 Instagram algorithm-weighted viral score predictor
- Claude-classified hook formula extraction across top performers
- Day × hour engagement heatmap with rolling smoothing (local timezone)
- 7-day post plan generator with compliance filtering
- Static HTML dashboard, zero-server architecture
- Two example niche presets: fashion-lifestyle, fitness-wellness
- SQLite-backed analytics layer with proper indexing
- CLI via `click` + `rich` (init / scrape / tiktok / analyze / plan / dashboard / refresh)
- 20-test pytest suite covering scoring, db, sound lifecycle
- GitHub Actions CI across Python 3.10/3.11/3.12 on Ubuntu + Windows
- MIT License, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md

### Stack
- Python 3.10+
- SQLite (local-first)
- Apify SDK, Anthropic SDK, TikTokApi
- Static HTML dashboard with vanilla CSS

[Unreleased]: https://github.com/TopStriker33/vyralforge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/TopStriker33/vyralforge/releases/tag/v0.1.0
