"""Vyral Forge CLI — single entry point.

Commands:
  python vyralforge.py init                       # setup DB
  python vyralforge.py scrape --niche fashion-lifestyle
  python vyralforge.py scrape-all                 # scrape every niche
  python vyralforge.py deepdive --niche fashion-lifestyle
  python vyralforge.py tiktok                     # pull TikTok trending sounds
  python vyralforge.py analyze                    # run all analyzers
  python vyralforge.py plan --niche fashion-lifestyle --theme "summer vibes"
  python vyralforge.py dashboard                  # render HTML + open
  python vyralforge.py refresh                    # full pipeline scrape→analyze
"""
from __future__ import annotations

from datetime import date, timedelta

import click
from rich.console import Console
from rich.table import Table

from config import NICHES
from database import init_db

console = Console()


@click.group()
def cli():
    """Vyral Forge — local virality engine."""


@cli.command()
def init():
    """Initialize SQLite database."""
    init_db()
    console.print("[green]✓[/green] database initialized at config.DB_PATH")


@cli.command()
@click.option("--niche", required=True, type=click.Choice(list(NICHES)))
@click.option("--per-tag", default=30, type=int)
def scrape(niche: str, per_tag: int):
    """Bulk-discover posts for a niche (Apify apidojo)."""
    from scrapers.apify_discover import discover_by_hashtags
    n = discover_by_hashtags(niche, per_tag)
    console.print(f"[green]✓[/green] discovered {n} posts for [bold]{niche}[/bold]")


@cli.command(name="scrape-all")
@click.option("--per-tag", default=30, type=int)
def scrape_all(per_tag: int):
    """Bulk-discover for every configured niche."""
    from scrapers.apify_discover import discover_by_hashtags
    total = 0
    for n in NICHES:
        c = discover_by_hashtags(n, per_tag)
        console.print(f"  {n}: {c}")
        total += c
    console.print(f"[green]✓[/green] total {total} posts")


@cli.command()
@click.option("--niche", required=True, type=click.Choice(list(NICHES)))
@click.option("--top", default=20, type=int)
def deepdive(niche: str, top: int):
    """Deep-dive top reels: transcripts + audio_id (Apify reel-scraper)."""
    from scrapers.apify_reels import deep_dive, top_candidates_for_deepdive
    cands = top_candidates_for_deepdive(niche, top)
    if not cands:
        console.print("[yellow]no candidates — run scrape first[/yellow]")
        return
    n = deep_dive(cands)
    console.print(f"[green]✓[/green] enriched {n} reels for [bold]{niche}[/bold]")


@cli.command()
@click.option("--count", default=50, type=int)
def tiktok(count: int):
    """Pull TikTok trending sounds (cross-platform J-3 radar)."""
    from scrapers.tiktok_trends import pull_tiktok_trends
    n = pull_tiktok_trends(count)
    console.print(f"[green]✓[/green] stored {n} TikTok rising sounds")


@cli.command()
def analyze():
    """Run all analyzers: viral_score → sounds lifecycle → timing heatmap → hooks."""
    from analyzer.hooks import extract_hooks
    from analyzer.sounds import refresh_lifecycle
    from analyzer.timing import build_heatmap
    from analyzer.viral_score import score_all_posts

    s = score_all_posts()
    console.print(f"  scored {s} posts")
    n_life = refresh_lifecycle()
    console.print(f"  refreshed {n_life} sound lifecycles")
    h = build_heatmap()
    console.print(f"  built {h} heatmap cells")
    for n in NICHES:
        try:
            c = extract_hooks(n, top_n=30)
            console.print(f"  hooks/{n}: {c}")
        except RuntimeError as e:
            console.print(f"  [yellow]hooks/{n}: skipped ({e})[/yellow]")
    console.print("[green]✓[/green] analyzers done")


@cli.command()
@click.option("--niche", required=True, type=click.Choice(list(NICHES)))
@click.option("--theme", default="general growth")
@click.option("--week", default=None, help="ISO date Mon of week (default: next Mon)")
def plan(niche: str, theme: str, week: str | None):
    """Generate 7-day viral post plan."""
    from planner.generate_week import generate_week
    if week:
        ws = date.fromisoformat(week)
    else:
        today = date.today()
        ws = today + timedelta(days=(7 - today.weekday()) % 7 or 7)

    p = generate_week(niche, ws, theme)
    console.print(f"\n[bold]Plan for {niche} — week of {ws} — theme: {theme}[/bold]\n")
    table = Table(show_lines=True)
    for col in ("Day", "Hour", "Hook", "Sound", "Caption", "OK"):
        table.add_column(col)
    for post in p["posts"]:
        c = post["concept"]
        ok = "✓" if post["compliance_ok"] else f"⚠ {','.join(post['compliance_issues'])}"
        table.add_row(
            f"{post['day_of_week']} {post['date']}",
            f"{post['hour']:02d}h",
            post["hook_formula"],
            (post["sound"]["title"] or "original")[:30],
            (c.get("caption", ""))[:80],
            ok,
        )
    console.print(table)


@cli.command()
def dashboard():
    """Render local HTML dashboard and open in browser."""
    from ui.render_dashboard import open_in_browser, render
    p = render()
    open_in_browser(p)
    console.print(f"[green]✓[/green] {p}")


@cli.command()
@click.option("--per-tag", default=20, type=int)
def refresh(per_tag: int):
    """Full pipeline: scrape → tiktok → analyze → dashboard."""
    from analyzer.hooks import extract_hooks
    from analyzer.sounds import refresh_lifecycle
    from analyzer.timing import build_heatmap
    from analyzer.viral_score import score_all_posts
    from scrapers.apify_discover import discover_by_hashtags
    from scrapers.tiktok_trends import pull_tiktok_trends
    from ui.render_dashboard import render

    init_db()
    for n in NICHES:
        try:
            c = discover_by_hashtags(n, per_tag)
            console.print(f"  scraped {n}: {c}")
        except Exception as e:
            console.print(f"  [red]scrape {n} failed: {e}[/red]")
    try:
        t = pull_tiktok_trends(50)
        console.print(f"  tiktok: {t}")
    except Exception as e:
        console.print(f"  [yellow]tiktok skipped: {e}[/yellow]")
    s = score_all_posts()
    console.print(f"  scored: {s}")
    refresh_lifecycle()
    build_heatmap()
    for n in NICHES:
        try:
            extract_hooks(n, top_n=30)
        except Exception as e:
            console.print(f"  [yellow]hooks/{n}: {e}[/yellow]")
    p = render()
    console.print(f"[green]✓[/green] refresh done · dashboard: {p}")


if __name__ == "__main__":
    cli()
