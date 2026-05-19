# Contributing to Vyral Forge

Thank you for considering a contribution. Vyral Forge is built for solo creators, and every PR helps level the playing field against agency tooling.

## Quick setup

```bash
git clone https://github.com/YOUR_USERNAME/vyralforge.git
cd vyralforge
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your test API keys
python vyralforge.py init
```

## What we welcome

**High-impact contributions:**
- 🎯 New niche presets in `config.py` (hashtag lists + seed accounts + compliance rules)
- 🔌 Additional Apify actor integrations
- 📊 Improved viral_score weights or proxy signals
- 🚫 New anti-pattern / distribution-flag detection rules
- 🎨 Dashboard UI improvements (the current one is functional but not pretty)
- 🌍 i18n / non-English niche support
- 🧪 Tests (we have very few — help us fix that)

**Also welcome:**
- Bug fixes (open an issue first if it's non-trivial)
- Documentation improvements
- Examples / tutorials
- Performance optimizations

**Out of scope (please don't PR these):**
- Anything that violates platform Terms of Service (mass DM bots, fake engagement, etc.)
- Closed-source dependencies
- Removing the open-source license or attribution

## Code style

- Python 3.10+ syntax (we use type hints, `|` unions, `from __future__ import annotations`)
- Run `ruff check .` before committing (we'll add this to CI soon)
- Keep modules small and single-purpose
- Comments explain *why*, not *what*

## Commit messages

Short, present tense, imperative. Examples:
- `Add fitness-wellness niche preset`
- `Fix Apify reel scraper handling null transcripts`
- `Bump viral_score DM weight to 0.32 per Mosseri update`

## Opening a PR

1. Fork the repo
2. Branch from `main`: `git checkout -b your-feature`
3. Make your change, commit, push
4. Open a PR with a clear description of the problem and the fix
5. Be patient — reviews happen in batches

## Code of conduct

Be kind. This project exists to help solo creators compete against systems that aren't designed for them. Don't be a system that isn't designed for new contributors.

If you want to discuss something before building, open an issue or a discussion first.

## License

By contributing, you agree your contributions will be licensed under the MIT License.
