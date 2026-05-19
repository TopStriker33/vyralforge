"""Render a static HTML dashboard from the SQLite data.

Opens in browser, no server required. Shows:
  - Top posts per niche
  - Rising sounds (with TikTok-first flag)
  - Hook formulas leaderboard
  - Timing heatmap
  - Latest week plan (if any)
"""
from __future__ import annotations
import json
import html
import webbrowser
from datetime import datetime
from pathlib import Path

from config import NICHES, ROOT
from database import conn
from analyzer.timing import DAY_NAMES

OUT = ROOT / "ui" / "dashboard.html"


def _fetch_all():
    data = {}
    with conn() as c:
        data["totals"] = dict(c.execute(
            "SELECT COUNT(*) as posts, "
            "(SELECT COUNT(*) FROM sounds) as sounds, "
            "(SELECT COUNT(*) FROM hooks) as hooks, "
            "(SELECT COUNT(*) FROM plans) as plans "
            "FROM posts"
        ).fetchone() or {})

        data["niches"] = {}
        for niche in NICHES:
            top = [dict(r) for r in c.execute(
                "SELECT id, owner_username, caption, viral_score, play_count, like_count, url "
                "FROM posts WHERE niche=? AND viral_score IS NOT NULL "
                "ORDER BY viral_score DESC LIMIT 15",
                (niche,),
            ).fetchall()]
            hooks = [dict(r) for r in c.execute(
                "SELECT formula, AVG(avg_score) as score, COUNT(*) as n, MAX(example) as example "
                "FROM hooks WHERE niche=? GROUP BY formula ORDER BY score DESC LIMIT 10",
                (niche,),
            ).fetchall()]
            heatmap = [dict(r) for r in c.execute(
                "SELECT day_of_week, hour_of_day, avg_score, sample_size FROM timing_heatmap "
                "WHERE niche=?",
                (niche,),
            ).fetchall()]
            latest_plan = c.execute(
                "SELECT plan_json, week_start, theme, created_at FROM plans "
                "WHERE niche=? ORDER BY created_at DESC LIMIT 1",
                (niche,),
            ).fetchone()
            data["niches"][niche] = {
                "label":   NICHES[niche]["label"],
                "top":     top,
                "hooks":   hooks,
                "heatmap": heatmap,
                "plan":    json.loads(latest_plan["plan_json"]) if latest_plan else None,
            }

        data["sounds"] = [dict(r) for r in c.execute(
            "SELECT audio_id, title, artist, lifecycle, usage_count, source, tiktok_first_seen "
            "FROM sounds WHERE lifecycle IN ('rising','peak') "
            "ORDER BY CASE lifecycle WHEN 'rising' THEN 0 ELSE 1 END, usage_count DESC LIMIT 30"
        ).fetchall()]
    return data


def _heatmap_grid(heatmap: list[dict]) -> str:
    grid = {(d, h): None for d in range(7) for h in range(24)}
    for row in heatmap:
        grid[(row["day_of_week"], row["hour_of_day"])] = row
    out = ["<table class='heatmap'><tr><th></th>"]
    out += [f"<th>{h:02d}</th>" for h in range(24)]
    out.append("</tr>")
    for d in range(7):
        out.append(f"<tr><th>{DAY_NAMES[d]}</th>")
        for h in range(24):
            cell = grid[(d, h)]
            if cell:
                v = cell["avg_score"]
                n = cell["sample_size"]
                alpha = min(v / 100, 1.0)
                out.append(f"<td style='background:rgba(232,93,117,{alpha:.2f})' title='score {v:.0f} (n={n})'>{int(v)}</td>")
            else:
                out.append("<td></td>")
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


def render() -> Path:
    data = _fetch_all()
    t = data["totals"]
    parts = [f"""<!DOCTYPE html><html><head>
<meta charset='utf-8'><title>Vyral Forge — Dashboard</title>
<style>
 body{{font:14px -apple-system,Segoe UI,sans-serif;background:#0d0d12;color:#e8e8ee;margin:0;padding:24px;}}
 h1{{font-size:28px;margin:0 0 4px;background:linear-gradient(90deg,#e85d75,#f4a261);-webkit-background-clip:text;color:transparent;}}
 h2{{font-size:18px;margin:32px 0 12px;color:#f4a261;border-bottom:1px solid #2a2a35;padding-bottom:6px;}}
 h3{{font-size:15px;margin:20px 0 8px;color:#e8e8ee;}}
 .meta{{color:#7a7a8a;font-size:12px;margin-bottom:24px;}}
 .stats{{display:flex;gap:24px;margin-bottom:24px;}}
 .stat{{background:#181822;padding:16px 24px;border-radius:8px;border:1px solid #2a2a35;}}
 .stat .n{{font-size:24px;font-weight:600;color:#e85d75;}}
 .stat .l{{font-size:11px;color:#7a7a8a;text-transform:uppercase;letter-spacing:1px;}}
 .niche{{background:#13131c;padding:20px;border-radius:8px;border:1px solid #2a2a35;margin-bottom:20px;}}
 table{{width:100%;border-collapse:collapse;font-size:13px;}}
 th,td{{padding:8px 10px;text-align:left;border-bottom:1px solid #2a2a35;}}
 th{{color:#7a7a8a;font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:1px;}}
 .score{{color:#e85d75;font-weight:600;}}
 .heatmap{{font-size:10px;}}
 .heatmap th{{padding:2px 4px;text-align:center;}}
 .heatmap td{{padding:6px;text-align:center;background:#1a1a25;color:#fff;min-width:22px;}}
 .pill{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:500;}}
 .pill-rising{{background:#1e4f3b;color:#5cd9a7;}}
 .pill-peak{{background:#4f3e1e;color:#f4c95c;}}
 .pill-tt{{background:#3b1e4f;color:#c95cf4;}}
 .pill-warn{{background:#4f1e1e;color:#f45c5c;}}
 .truncate{{max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
 a{{color:#e85d75;text-decoration:none;}}
 a:hover{{text-decoration:underline;}}
 .post-card{{background:#181822;padding:14px;border-radius:6px;margin-bottom:10px;border-left:3px solid #e85d75;}}
 .post-card .day{{color:#f4a261;font-weight:600;font-size:13px;}}
 .post-card .hook{{color:#7a7a8a;font-size:11px;margin:4px 0;}}
 .post-card .caption{{font-size:13px;margin:6px 0;}}
 .post-card .meta{{font-size:11px;color:#5a5a6a;margin:0;}}
</style></head><body>
<h1>Vyral Forge</h1>
<div class='meta'>Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} · local virality engine</div>
<div class='stats'>
 <div class='stat'><div class='n'>{t.get('posts',0)}</div><div class='l'>posts</div></div>
 <div class='stat'><div class='n'>{t.get('sounds',0)}</div><div class='l'>sounds</div></div>
 <div class='stat'><div class='n'>{t.get('hooks',0)}</div><div class='l'>hooks</div></div>
 <div class='stat'><div class='n'>{t.get('plans',0)}</div><div class='l'>plans</div></div>
</div>
"""]

    # Sounds panel
    parts.append("<h2>🎵 Rising sounds (cross-platform radar)</h2><table><tr><th>Lifecycle</th><th>Source</th><th>Title</th><th>Artist</th><th>Usage</th></tr>")
    for s in data["sounds"]:
        tt_flag = " <span class='pill pill-tt'>TT-first</span>" if s["tiktok_first_seen"] else ""
        pill_cls = "pill-rising" if s["lifecycle"] == "rising" else "pill-peak"
        parts.append(f"<tr><td><span class='pill {pill_cls}'>{s['lifecycle']}</span>{tt_flag}</td>"
                     f"<td>{html.escape(s.get('source') or '')}</td>"
                     f"<td>{html.escape(s.get('title') or '')}</td>"
                     f"<td>{html.escape(s.get('artist') or '')}</td>"
                     f"<td>{s['usage_count']}</td></tr>")
    parts.append("</table>")

    # Per-niche panels
    for niche, nd in data["niches"].items():
        parts.append(f"<div class='niche'><h2>{html.escape(nd['label'])} <span style='font-size:12px;color:#5a5a6a'>({niche})</span></h2>")

        parts.append("<h3>Top hooks</h3><table><tr><th>Formula</th><th>Avg score</th><th>Sample size</th><th>Example</th></tr>")
        for h in nd["hooks"]:
            parts.append(f"<tr><td>{html.escape(h['formula'])}</td>"
                         f"<td class='score'>{h['score']:.1f}</td>"
                         f"<td>{h['n']}</td>"
                         f"<td class='truncate'>{html.escape(h.get('example') or '')}</td></tr>")
        parts.append("</table>")

        parts.append("<h3>Timing heatmap (Europe/Zurich)</h3>")
        parts.append(_heatmap_grid(nd["heatmap"]))

        parts.append("<h3>Top viral posts</h3><table><tr><th>Score</th><th>User</th><th>Caption</th><th>Plays</th><th>Likes</th><th></th></tr>")
        for p in nd["top"]:
            parts.append(f"<tr><td class='score'>{p['viral_score']:.0f}</td>"
                         f"<td>@{html.escape(p['owner_username'] or '')}</td>"
                         f"<td class='truncate'>{html.escape((p.get('caption') or '')[:120])}</td>"
                         f"<td>{p.get('play_count') or '—'}</td>"
                         f"<td>{p.get('like_count') or '—'}</td>"
                         f"<td><a href='{html.escape(p.get('url') or '#')}' target='_blank'>↗</a></td></tr>")
        parts.append("</table>")

        if nd["plan"]:
            parts.append(f"<h3>Latest week plan — {nd['plan']['week_start']} · theme: {html.escape(nd['plan']['theme'])}</h3>")
            for post in nd["plan"]["posts"]:
                c = post["concept"]
                warn = ""
                if not post["compliance_ok"]:
                    warn = f" <span class='pill pill-warn'>⚠ {', '.join(post['compliance_issues'])}</span>"
                parts.append(f"<div class='post-card'>"
                             f"<div class='day'>{post['day_of_week']} {post['date']} · {post['hour']:02d}h{warn}</div>"
                             f"<div class='hook'>Hook: <b>{html.escape(post['hook_formula'])}</b> · Sound: {html.escape(post['sound']['title'] or 'original')}</div>"
                             f"<div class='caption'><b>First frame:</b> {html.escape(c.get('first_frame',''))}</div>"
                             f"<div class='caption'>{html.escape(c.get('caption',''))}</div>"
                             f"<div class='meta'>{' '.join('#' + h for h in c.get('hashtags', []))}  ·  CTA: {html.escape(c.get('cta_type',''))}</div>"
                             f"</div>")
        parts.append("</div>")

    parts.append("</body></html>")
    OUT.write_text("".join(parts), encoding="utf-8")
    return OUT


def open_in_browser(path: Path = OUT) -> None:
    webbrowser.open(path.resolve().as_uri())


if __name__ == "__main__":
    p = render()
    print(f"[dashboard] {p}")
    open_in_browser(p)
