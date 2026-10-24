"""Fetch real public GitHub contribution counts without a token."""
import argparse
import json
import re
from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from .common import ROOT, atomic_write, load_profile
except ImportError:
    from common import ROOT, atomic_write, load_profile

LEGACY_LEVELS = {
    '#ebedf0': 0, '#161b22': 0,
    '#9be9a8': 1, '#40c463': 2, '#30a14e': 3, '#216e39': 4,
    '#c6e48b': 1, '#7bc96f': 2, '#239a3b': 3, '#196127': 4,
    '#0e4429': 1, '#006d32': 2, '#26a641': 3, '#39d353': 4,
}


def parse_contributions(html):
    soup = BeautifulSoup(html, 'html.parser')
    tooltips = {tip.get('for'): tip.get_text(' ', strip=True)
                for tip in soup.find_all('tool-tip')}
    days = {}
    for cell in soup.select('[data-date]'):
        stamp = cell['data-date']
        date.fromisoformat(stamp)
        raw_level = cell.get('data-level')
        level = int(raw_level) if raw_level is not None else None
        if level is not None and not 0 <= level <= 4:
            raise ValueError(f'Unrecognized GitHub contribution level: {level}')
        count = cell.get('data-count')
        if count is None:
            label = tooltips.get(cell.get('id'), '') or cell.get('aria-label', '')
            match = re.match(r'^\s*(No|[\d,]+)\s+contributions?\b', label, re.I)
            if match:
                count = '0' if match[1].lower() == 'no' else match[1].replace(',', '')
            elif cell.get('data-level') == '0':
                count = '0'
            else:
                raise ValueError(f'Missing contribution count for {stamp}; GitHub HTML may have changed.')
        if not re.fullmatch(r'\d+', str(count)):
            raise ValueError(f'Invalid count on {stamp}: {count!r}')
        count = int(count)
        if level is None:
            level = 0 if count == 0 else LEGACY_LEVELS.get(cell.get('fill', '').lower())
        if level is None or (count > 0) != (level > 0):
            raise ValueError(f'Unknown or inconsistent contribution level on {stamp}; refusing to hide activity.')
        day = {'date': stamp, 'count': count, 'level': level}
        if stamp in days and days[stamp] != day:
            raise ValueError(f'Conflicting duplicate date: {stamp}')
        days[stamp] = day
    if not days:
        raise ValueError('No contribution cells found; refusing to replace the last good data.')
    return sorted(days.values(), key=lambda day: day['date'])


def compute_stats(days, end):
    by_date = {date.fromisoformat(day['date']): day for day in days
               if date.fromisoformat(day['date']) <= end}
    ordered = sorted(by_date.items())
    monthly = {}
    longest = run = 0
    previous = None
    best = None
    total = active = 0
    for stamp, day in ordered:
        count = day['count']
        total += count
        month = stamp.strftime('%Y-%m')
        monthly[month] = monthly.get(month, 0) + count
        if count:
            active += 1
            run = run + 1 if previous == stamp - timedelta(days=1) else 1
            longest = max(longest, run)
            if best is None or count > best['count']:
                best = {'date': stamp.isoformat(), 'count': count}
        else:
            run = 0
        previous = stamp
    anchor = end if by_date.get(end, {}).get('count', 0) else end - timedelta(days=1)
    current = 0
    while by_date.get(anchor, {}).get('count', 0):
        current += 1
        anchor -= timedelta(days=1)
    return {'total': total, 'active_days': active, 'current_streak': current,
            'longest_streak': longest, 'best_day': best, 'monthly_totals': monthly}


def build_payload(username, days, end):
    start = end - timedelta(days=364)
    by_date = {}
    for day in days:
        stamp = date.fromisoformat(day['date'])
        if not start <= stamp <= end:
            continue
        if type(day['count']) is not int or day['count'] < 0 or type(day['level']) is not int or not 0 <= day['level'] <= 4:
            raise ValueError(f'Invalid daily record: {day}')
        if (day['count'] > 0) != (day['level'] > 0):
            raise ValueError(f'Contribution count and color level disagree on {stamp}.')
        if stamp in by_date and by_date[stamp] != day:
            raise ValueError(f'Conflicting daily records: {stamp}')
        by_date[stamp] = day
    expected = [start + timedelta(days=i) for i in range(365)]
    missing = [stamp.isoformat() for stamp in expected if stamp not in by_date]
    if missing:
        raise ValueError(f'Incomplete calendar: {len(missing)} missing days, first: {missing[0]}. Keeping previous data.')
    selected = [by_date[stamp] for stamp in expected]
    return {'schema_version': 1, 'username': username,
            'source': f'https://github.com/users/{username}/contributions',
            'as_of': end.isoformat(),
            'range': {'start': start.isoformat(), 'end': end.isoformat()},
            'days': selected, 'stats': compute_stats(selected, end)}


def fetch_contributions(username, end):
    start = end - timedelta(days=364)
    records = []
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    with requests.Session() as session:
        session.mount('https://', HTTPAdapter(max_retries=retry))
        session.headers.update({'User-Agent': 'terminal-profile-art/1.0', 'Accept-Language': 'en-US,en;q=0.9'})
        for year in range(start.year, end.year + 1):
            # This endpoint chooses a calendar year, not an arbitrary cross-year window.
            response = session.get(f'https://github.com/users/{username}/contributions',
                                   params={'from': f'{year}-01-01', 'to': f'{year}-12-31'}, timeout=30)
            response.raise_for_status()
            records.extend(parse_contributions(response.text))
    return build_payload(username, records, end)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=str)
    parser.add_argument('--username', help='Override profile.json username')
    parser.add_argument('--end', type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    parser.add_argument('--output', type=str, default=str(ROOT / 'data/contributions.json'))
    args = parser.parse_args()
    username = args.username or load_profile(args.config)['username']
    # Validate command-line usernames with the same rule as configuration.
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', username):
        parser.error('Invalid GitHub username')
    try:
        payload = fetch_contributions(username, args.end)
        atomic_write(args.output, json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    except (requests.RequestException, ValueError) as error:
        parser.exit(1, f'Contribution fetch failed: {error}\n')
    print(f"Saved {len(payload['days'])} real days for @{username}: {payload['stats']['total']:,} contributions.")


if __name__ == '__main__':
    main()
