"""Render a real 53-week calendar as a self-contained animated SVG."""
import argparse
import json
from datetime import date, timedelta
from html import escape
from pathlib import Path

try:
    from .common import ROOT, FG, GREEN, MUTED, atomic_write, static_mode, svg_end, svg_start
    from .fetch_contributions import build_payload
except ImportError:
    from common import ROOT, FG, GREEN, MUTED, atomic_write, static_mode, svg_end, svg_start
    from fetch_contributions import build_payload

PALETTE = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353', '#69f0a0']


def render_heatmap(payload, static=False):
    # Recompute statistics and check coverage even for manually edited input JSON.
    payload = build_payload(payload['username'], payload['days'], date.fromisoformat(payload['range']['end']))
    start = date.fromisoformat(payload['range']['start'])
    end = date.fromisoformat(payload['range']['end'])
    grid_start = start - timedelta(days=(start.weekday() + 1) % 7)
    days = {day['date']: day for day in payload['days']}
    stats = payload['stats']
    parts = svg_start(860, 326, f"Contribution calendar for {payload['username']}",
                      f"{stats['total']:,} contributions in the last year, {start} through {end}. Public GitHub data. Longest streak in this interval: {stats['longest_streak']} days.", 'contributions.sh')
    if not static:
        parts.append('<style>@keyframes tile-in{from{opacity:0;transform:translate(-5px,-5px)}to{opacity:1;transform:translate(0,0)}}.tile{animation:tile-in .38s cubic-bezier(.22,.68,0,1) both}</style>')
    parts.extend([
        f'<text x="24" y="68" font-size="11" fill="{GREEN}">$ git log --last-year</text>',
        f'<text x="836" y="68" text-anchor="end" font-size="10" fill="{MUTED}">@{escape(payload["username"])} / 53 weeks</text>',
    ])
    left, top, step, size = 61, 104, 14.5, 11
    for weekday, label in [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]:
        parts.append(f'<text x="24" y="{top + weekday * step + 8:g}" font-size="9" fill="{MUTED}">{label}</text>')
    previous_month = None
    for week in range(53):
        week_start = grid_start + timedelta(weeks=week)
        # Label the first visible occurrence of a month when there is room.
        visible_start = max(start, week_start)
        month = (visible_start.year, visible_start.month)
        if visible_start <= end and month != previous_month:
            if week <= 50:
                parts.append(f'<text x="{left + week * step:g}" y="92" font-size="9" fill="{MUTED}">{visible_start.strftime("%b")}</text>')
            previous_month = month
        for weekday in range(7):
            stamp = week_start + timedelta(days=weekday)
            day = days.get(stamp.isoformat())
            x, y = left + week * step, top + weekday * step
            if day is None:
                parts.append(f'<rect x="{x:g}" y="{y:g}" width="{size}" height="{size}" rx="2.5" fill="none" stroke="#17212b" stroke-dasharray="2 2"/>')
                continue
            # Keep GitHub's own quantile levels. The optional fifth green is
            # reserved for the interval's actual maximum, never a fake count.
            level = day['level']
            color = PALETTE[5] if level == 4 and stats['best_day'] and day['count'] == stats['best_day']['count'] else PALETTE[level]
            animation = f' class="tile" style="animation-delay:{week * .018 + weekday * .035:.3f}s"' if not static else ''
            parts.append(f'<rect x="{x:g}" y="{y:g}" width="{size}" height="{size}" rx="2.5" fill="{color}" data-date="{stamp}" data-count="{day["count"]}" data-level="{level}"{animation}>'
                         f'<title>{day["count"]:,} contributions on {stamp}</title></rect>')
    parts.extend([
        f'<text x="61" y="229" font-size="10" fill="{FG}">{stats["total"]:,} contributions in the last year</text>',
        f'<text x="650" y="229" font-size="9" fill="{MUTED}">Less</text>',
    ])
    for index, color in enumerate(PALETTE):
        parts.append(f'<rect x="{682 + index * 17}" y="220" width="11" height="11" rx="2.5" fill="{color}"/>')
    parts.extend([
        f'<text x="789" y="229" font-size="9" fill="{MUTED}">More</text>',
        '<path d="M24 247H836" stroke="#202b37"/>',
    ])
    for x, value, label in [(24, f'{stats["current_streak"]}d', 'CURRENT STREAK'),
                            (242, f'{stats["longest_streak"]}d', 'LONGEST / YEAR'),
                            (465, str(stats['active_days']), 'ACTIVE DAYS')]:
        parts.append(f'<text x="{x}" y="274" font-size="18" font-weight="700" fill="{GREEN}">{value}</text>'
                     f'<text x="{x}" y="293" font-size="8.5" letter-spacing="1" fill="{MUTED}">{label}</text>')
    parts.extend([
        f'<text x="836" y="273" text-anchor="end" font-size="9" fill="{MUTED}">{start} → {end}</text>',
        f'<text x="836" y="293" text-anchor="end" font-size="9" fill="{MUTED}">public activity / refreshed daily</text>',
        f'<text x="24" y="315" font-size="8" fill="{MUTED}">UTC window · current streak allows an unfinished today</text>',
    ])
    return svg_end(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data/contributions.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'contrib-heatmap.svg')
    parser.add_argument('--static', action='store_true')
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding='utf-8'))
        atomic_write(args.output, render_heatmap(payload, static_mode(args.static)))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Heatmap generation failed: {error}\n')
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
