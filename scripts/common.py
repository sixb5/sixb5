"""Configuration, atomic writes, and the shared terminal SVG frame."""
import json
import os
import re
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT = "'DejaVu Sans Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace"
BG = '#0b1017'
FG = '#c9d5e2'
MUTED = '#7c8b9d'
GREEN = '#69f0a0'


def load_profile(path=None):
    profile = json.loads(Path(path or ROOT / 'profile.json').read_text(encoding='utf-8'))
    username = profile.get('username', '')
    if not isinstance(username, str) or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', username):
        raise ValueError('profile.json requires a valid GitHub username (1–39 characters).')
    return profile


def atomic_write(path, content):
    """Do not damage the last good artifact on interrupted/failed generation."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding='utf-8') == content:
        return
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                     dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(content)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def static_mode(flag=False):
    return flag or os.environ.get('STATIC', '') == '1'


def svg_start(width, height, title, description, filename):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title>',
        f'<desc id="desc">{escape(description)}</desc>',
        '<style>text{font-family:' + FONT + '} .muted{fill:' + MUTED + '}',
        '@media(prefers-reduced-motion:reduce){.enter,.tile{animation:none!important;opacity:1!important;transform:none!important}.row-reveal{clip-path:none!important}.cursor{display:none!important}}</style>',
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="{BG}" stroke="#25303d"/>',
        f'<path d="M1 40.5H{width - 1}" stroke="#202b37"/>',
        '<circle cx="19" cy="21" r="4" fill="#f07883"/><circle cx="34" cy="21" r="4" fill="#e4bd6c"/><circle cx="49" cy="21" r="4" fill="#69c993"/>',
        f'<text x="{width / 2 + 17:g}" y="25" text-anchor="middle" font-size="10" fill="{MUTED}">{escape(filename)}</text>',
    ]


def svg_end(parts):
    return '\n'.join([*parts, '</svg>', ''])
