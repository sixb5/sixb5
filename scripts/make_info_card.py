"""Render configurable Neofetch-style profile information with one-shot reveals."""
import argparse
import textwrap
from html import escape
from pathlib import Path

try:
    from .common import ROOT, FG, GREEN, MUTED, atomic_write, load_profile, static_mode, svg_end, svg_start
except ImportError:
    from common import ROOT, FG, GREEN, MUTED, atomic_write, load_profile, static_mode, svg_end, svg_start


def render_info(profile, static=False):
    fields = []
    for row in profile.get('rows', []):
        values = row['value'] if isinstance(row['value'], list) else [row['value']]
        lines = [line for value in values for line in textwrap.wrap(str(value), 40) or ['']]
        fields.append((str(row['label']), lines))
    content_height = sum(len(lines) * 22 + 12 for _, lines in fields)
    height = max(440, 190 + content_height + 90)
    parts = svg_start(490, height, f"{profile.get('name', profile['username'])} — profile information",
                      'Neofetch-style profile information. ' + '; '.join(label + ': ' + ', '.join(lines) for label, lines in fields), 'whoami.sh')
    if not static:
        parts.append('<style>@keyframes line-in{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}.enter{animation:line-in .42s ease-out both}</style>')
    index = 0

    def line(content):
        nonlocal index
        animation = f' class="enter" style="animation-delay:{.25 + index * .13:.2f}s"' if not static else ''
        parts.append(f'<g{animation}>{content}</g>')
        index += 1

    line(f'<text x="24" y="68" font-size="11" fill="{GREEN}">$ neofetch --user</text>')
    name = str(profile.get('name', profile['username']))
    name_size = min(24, 430 / max(1, len(name)) / .61)
    line(f'<text x="24" y="109" font-size="{name_size:.2f}" font-weight="700" fill="{FG}">{escape(name)}</text>'
         f'<text x="24" y="132" font-size="11" fill="{MUTED}">{escape(profile["username"])}@github</text>')
    line('<path d="M24 148H466" stroke="#25303d"/>')
    subtitle = textwrap.shorten(str(profile.get('subtitle', '')), width=58, placeholder='…')
    line(f'<text x="24" y="170" font-size="10.5" fill="{MUTED}">{escape(subtitle)}</text>')
    y = 202
    for label, lines in fields:
        for number, value in enumerate(lines):
            label_text = escape(label[:12]) + ':' if number == 0 else ''
            line(f'<text x="24" y="{y}" font-size="11.5" fill="{GREEN}">{label_text}</text>'
                 f'<text x="145" y="{y}" font-size="11.5" fill="{FG}">{escape(value)}</text>')
            y += 22
        y += 12
    swatches = ''.join(f'<rect x="{24 + i * 22}" y="{height - 75}" width="22" height="12" fill="{color}"/>'
                       for i, color in enumerate(['#183b2a', '#20683f', '#279650', '#39c76a', '#69f0a0', '#b1f5ca']))
    line(swatches)
    footer = textwrap.shorten(str(profile.get('footer', '')), width=61, placeholder='…')
    line(f'<path d="M24 {height - 42}H466" stroke="#202b37"/>'
         f'<text x="24" y="{height - 21}" font-size="9" fill="{MUTED}">{escape(footer)}</text>')
    return svg_end(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'info-card.svg')
    parser.add_argument('--static', action='store_true')
    args = parser.parse_args()
    atomic_write(args.output, render_info(load_profile(args.config), static_mode(args.static)))
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
