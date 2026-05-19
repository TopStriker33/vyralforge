# Vyral Forge

> Local-first virality engine for short-form video creators. Scrapes top performers per niche, extracts viral patterns (hooks, sounds, posting timing), then generates data-driven 7-day posting plans with AI-assisted captions. 100% local, no SaaS lock-in.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/TopStriker33/vyralforge/actions/workflows/ci.yml/badge.svg)](https://github.com/TopStriker33/vyralforge/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-20%20passing-brightgreen.svg)](https://github.com/TopStriker33/vyralforge/tree/main/tests)
[![Made for creators](https://img.shields.io/badge/built%20for-solo%20creators-ff69b4.svg)](https://github.com/TopStriker33/vyralforge)

## Why this exists

If you're a solo creator on Instagram / TikTok, the only way to compete with agencies right now is:
- Subscribe to **$200-1000/mo** SaaS tools (Metricool, Iconosquare, Exolyt, Trendpop)
- Or **fly blind** — guess at hooks, guess at sounds, guess at timing

This project is the middle path: **a local Python toolkit that gives you agency-grade content analytics for under $60/mo in API costs**, fully under your control.

It scrapes the top performers in *your* niche on Instagram (and watches TikTok for sound trends 48-72h before they hit Reels), extracts what's actually working in 2026's algorithm — and turns that into a 7-day posting plan you can ship.

## What it does

- 🔍 **Discover** — bulk-scrape top posts/Reels for a niche via the Apify ecosystem
- 🎤 **Deep-dive** — pull transcripts + audio_id on the top 5-10% (Apify reel scraper)
- 📡 **TikTok radar** — cross-platform sound trend detection 48-72h ahead of Reels adoption
- 📊 **Score** — viral_score predictor using 2026 Instagram algorithm weights (DM-sends > watch_time > saves > 3-sec hold)
- 🪝 **Hooks** — Claude-classified hook formulas across your top performers (10 known + emergent)
- ⏰ **Timing** — day × hour engagement heatmap, smoothed, in your local timezone
- 📅 **Plan** — 7-post weekly plan generator (day, hour, hook, sound, concept, caption, hashtags, CTA) with compliance check
- 🖥 **Dashboard** — static HTML dashboard, opens in browser, zero server required

## Stack

| Layer | Tool | Cost |
|---|---|---|
| Bulk scraper | Apify `apidojo/instagram-scraper` | ~$0.50 / 1k posts |
| Deep enrichment | Apify `apify/instagram-reel-scraper` (transcripts + audio_id) | ~$1.00 / 1k posts |
| Sound trend radar | [`TikTokApi`](https://github.com/davidteather/TikTok-Api) (OSS) | free |
| LLM analysis | Claude Sonnet 4.6 via Anthropic API | ~$5 / month typical |
| Storage | SQLite | free |
| UI | Static HTML + CLI (`rich` + `click`) | free |

**Estimated monthly cost**: $50–70 for ~30k posts/month of analysis.

## Quick start

### 1. Install

```bash
git clone https://github.com/TopStriker33/vyralforge.git
cd vyralforge
python -m venv .venv
source .venv/bin/activate    # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install            # only if you want the TikTok trend radar
```

### 2. Configure

```bash
cp .env.example .env
# edit .env with your API keys
```

You'll need:
- **Apify token** — free signup at [apify.com](https://apify.com) ($5 starter credit ≈ 10k posts)
- **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com)
- *(optional)* **TikTok ms_token** — extract from your logged-in browser cookies (refreshes every few days)

### 3. Define your niches

Open `config.py` and customize the `NICHES` dict to match your verticals. Each niche is a bundle of:
- Seed hashtags (used for discovery scraping)
- Seed accounts (specific creators to deep-dive)
- Content angle (free-form description, used in LLM prompts)
- Compliance rules (caption length, max hashtags, ban-words)

Two example presets are included (fashion-lifestyle, fitness-wellness). Replace or extend.

### 4. Run

```bash
python vyralforge.py init                                    # one-time DB bootstrap
python vyralforge.py refresh                                 # full pipeline
# OR step-by-step:
python vyralforge.py scrape-all --per-tag 30
python vyralforge.py tiktok --count 50
python vyralforge.py analyze
python vyralforge.py plan --niche fashion-lifestyle --theme "summer launch"
python vyralforge.py dashboard
```

Windows users: prefix commands with `$env:PYTHONIOENCODING="utf-8"; ` to avoid cp1252 encoding errors on unicode output.

## Project layout

```
vyralforge/
├── config.py                    # niches, API keys, score weights, compliance
├── vyralforge.py                # CLI entry point
├── database/
│   ├── schema.sql               # SQLite schema (posts, sounds, hooks, plans)
│   └── db.py                    # connection + upsert helpers
├── scrapers/
│   ├── apify_discover.py        # bulk discovery via hashtag/account
│   ├── apify_reels.py           # transcript + audio_id deep dive
│   └── tiktok_trends.py         # cross-platform sound radar
├── analyzer/
│   ├── viral_score.py           # 2026 algo-weighted score predictor
│   ├── hooks.py                 # Claude-classified hook formulas
│   ├── sounds.py                # rising / peak / dying / dead classifier
│   └── timing.py                # day×hour engagement heatmap
├── planner/
│   ├── generate_week.py         # 7-day plan generator
│   └── llm_brain.py             # Claude prompts (caption + concept gen)
├── ui/
│   ├── render_dashboard.py      # static HTML output
│   └── dashboard.html           # generated, opens in browser (gitignored)
└── data/
    └── vyral.db                 # SQLite (gitignored)
```

## How the viral_score works

Score weights are pulled from public 2026 Instagram algorithm research (Mosseri's confirmations, Later/Buffer/Sprout Social analysis):

```python
SCORE_WEIGHTS = {
    "dm_sends_per_reach":   0.30,   # #1 signal in 2026
    "watch_time_seconds":   0.20,
    "saves_per_reach":      0.15,
    "hold_rate_3s":         0.15,
    "completion_rate":      0.10,
    "comment_depth":        0.05,
    "profile_clicks":       0.03,
    "likes_per_reach":      0.02,
}
```

Since Instagram removed public view counts in 2024 and `save_count` / `share_count` are login-only, we use proxy signals where needed (see `analyzer/viral_score.py` for the full math). Tune the weights to match your niche's actual signal distribution.

## Sound trend radar (the unique feature)

Sounds rise on TikTok 48-72h before they're adopted en masse on Instagram Reels. By scraping TikTok's trending feed and cross-referencing with Apify Instagram data, Vyral Forge can flag a sound while it's still in the 5-50k uses sweet spot — before saturation.

The planner picks "rising" sounds with TikTok-first detection by default. See `analyzer/sounds.py` for the lifecycle classifier (`rising` → `peak` → `dying` → `dead`).

## Roadmap

- [x] Phase 1 — Instagram discovery + scoring + planning (current)
- [ ] Phase 2 — Multi-account scheduler (Metricool / Meta Graph API integration)
- [ ] Phase 3 — Native TikTok analytics (TikTok Business API)
- [ ] Phase 4 — AI gen pipeline integration (ComfyUI / Flux LoRA for content multiplier)
- [ ] Phase 5 — X (Twitter) virality engine port
- [ ] Phase 6 — Multi-creator collaboration layer (VA permissions, approval queues)

## Development

```bash
pip install -r requirements-dev.txt   # pytest + ruff
pytest tests/                          # run the 20-test suite
ruff check .                           # lint
```

CI runs on every push across Python 3.10/3.11/3.12 on Ubuntu + Windows. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and conventions.

Especially welcome:
- New niche presets (with hashtag lists + seed accounts)
- Additional Apify actor integrations
- Anti-pattern detection rules for new platforms
- UI improvements to the dashboard

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

Built on top of the work of: [`apify-client`](https://github.com/apify/apify-client-python), [`TikTok-Api`](https://github.com/davidteather/TikTok-Api) by David Teather, [`instagrapi`](https://github.com/subzeroid/instagrapi) by subzeroid (referenced as fallback option), [`anthropic`](https://github.com/anthropics/anthropic-sdk-python), [`click`](https://github.com/pallets/click), [`rich`](https://github.com/Textualize/rich).

Algorithm intelligence aggregated from public 2026 sources: Later, Buffer, Hootsuite, Sprout Social, Adam Mosseri's public statements.

---

**Note**: this is a research and analytics tool. You are responsible for complying with the Terms of Service of any platform you scrape. Apify operates within the legal framework established by *Meta v. Bright Data* (2024) for public, unauthenticated data. Do not use this toolkit to violate platform policies, harass users, or distribute content you don't own.
