"""Convert a prepared photo into monochrome, row-typed SVG artwork."""
import argparse
from html import escape
from pathlib import Path

from PIL import Image, ImageOps

try:
    from .common import ROOT, FG, GREEN, MUTED, atomic_write, load_profile, static_mode, svg_end, svg_start
except ImportError:
    from common import ROOT, FG, GREEN, MUTED, atomic_write, load_profile, static_mode, svg_end, svg_start

RAMP = ' .`:-=+*cs#%@'


def image_to_rows(image, columns=80, rows=46):
    if not 2 <= columns <= 160 or not 1 <= rows <= 100:
        raise ValueError('Use 2–160 columns and 1–100 rows.')
    # Character cells are taller than wide; contain avoids stretching the subject.
    target = (columns * 6, rows * 10)
    gray = ImageOps.contain(image.convert('L'), target, Image.Resampling.LANCZOS)
    canvas = Image.new('L', target, 255)
    canvas.paste(gray, ((target[0] - gray.width) // 2, (target[1] - gray.height) // 2))
    pixels = canvas.resize((columns, rows), Image.Resampling.LANCZOS)
    return [''.join(RAMP[round((255 - pixels.getpixel((x, y))) * (len(RAMP) - 1) / 255)]
                    for x in range(columns)) for y in range(rows)]


def render_ascii(rows, username, static=False):
    if not rows or not any(rows):
        raise ValueError('Portrait must contain at least one nonempty row.')
    columns = max(map(len, rows))
    width, height = 370, 440
    # A monospace advance is ~0.602 em. Constrain both axes, then use those
    # same physical cells for text, reveal clips and cursor movement.
    font_size = min(12, 322 / columns / .602, 276 / len(rows))
    char_width = font_size * .602
    line_height = font_size
    span = columns * char_width
    left = (width - span) / 2
    top = 105 + (276 - len(rows) * line_height) / 2
    parts = svg_start(width, height, f'ASCII portrait of {username}',
                      f'Monochrome portrait, {columns} columns by {len(rows)} rows. Each row types once from left to right.', 'portrait.sh')
    parts.extend([
        f'<text x="22" y="68" font-size="11" fill="{GREEN}">$ cat portrait.ascii</text>',
        f'<text x="22" y="87" font-size="9" fill="{MUTED}">{columns} columns / {len(rows)} lines / monochrome</text>',
    ])
    for index, row in enumerate(rows):
        baseline = top + (index + 1) * line_height
        delay = .15 + index * .045
        duration = delay + .18
        if not static:
            parts.append(f'<defs><clipPath id="row-{index}"><rect x="{left:.3f}" y="{baseline - line_height:.3f}" width="{span:.3f}" height="{line_height + 1:.3f}">'
                         f'<animate attributeName="width" values="0;0;{span:.3f}" keyTimes="0;{delay / duration:.6f};1" begin="0s" dur="{duration:.3f}s" fill="freeze"/>'
                         '</rect></clipPath></defs>')
        clip = f' clip-path="url(#row-{index})"' if not static else ''
        # xml:space is essential: SVG otherwise collapses the blank background.
        parts.append(f'<g class="row-reveal"{clip}><text x="{left:.3f}" y="{baseline:.3f}" fill="{FG}" font-size="{font_size:.4f}" xml:space="preserve">{escape(row)}</text></g>')
        if not static:
            parts.append(f'<rect class="cursor" x="{left:.3f}" y="{baseline - line_height + 1:.3f}" width="{char_width:.3f}" height="{line_height:.3f}" fill="{GREEN}" visibility="hidden">'
                         f'<set attributeName="visibility" to="visible" begin="{delay:.3f}s" dur=".18s"/>'
                         f'<animate attributeName="x" from="{left:.3f}" to="{left + span - char_width:.3f}" begin="{delay:.3f}s" dur=".18s"/>'
                         '</rect>')
    parts.extend([
        '<path d="M22 398H348" stroke="#202b37"/>',
        f'<text x="22" y="419" font-size="9" fill="{MUTED}">a face, rendered in characters.</text>',
        f'<text x="348" y="419" text-anchor="end" font-size="9" fill="{GREEN}">[ok]</text>',
    ])
    return svg_end(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'avi-ascii.svg')
    parser.add_argument('--static', action='store_true')
    args = parser.parse_args()
    profile = load_profile(args.config)
    settings = profile.get('portrait', {})
    source = args.input or ROOT / settings.get('source', 'source-prepped.png')
    try:
        with Image.open(source) as image:
            rows = image_to_rows(image, settings.get('columns', 80), settings.get('rows', 46))
        atomic_write(args.output, render_ascii(rows, profile['username'], static_mode(args.static)))
    except (OSError, ValueError) as error:
        parser.exit(1, f'ASCII generation failed: {error}\nRun: python scripts/prep_photo.py source-photo.png\n')
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
