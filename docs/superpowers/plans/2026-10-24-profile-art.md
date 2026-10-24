# Terminal Profile Art Implementation Plan

> **For agentic workers:** Execute the supplied specification in the current session. Use the test-driven-development and verification-before-completion skills for data correctness.

**Goal:** Deliver locally generated terminal SVG profile art for `sixb5` and daily refresh automation.

**Architecture:** Shared configuration and SVG helpers support independent portrait,
info-card, fetch, and heatmap scripts. GitHub HTML is parsed into validated daily
records before atomic JSON replacement; rendering consumes those records.

**Tech Stack:** Python 3.11+, requests, BeautifulSoup, optional local photo tools.

**Spec:** ../specs/2026-10-24-profile-art-design.md

## Global Constraints

- Exact artifacts: avi-ascii.svg, info-card.svg, contrib-heatmap.svg, README.md.
- Display 53 weeks by 7 days; only real in-range records count toward statistics.
- Widths: heatmap 860; portrait 370; info card 490.
- One-shot inline animation, static mode, accessible SVG text, no external assets.
- Daily dependencies: requests==2.32.3, beautifulsoup4==4.12.3.

## Review Focus

- HTML tooltip counts, legacy rect counts, thousands separators, and missing counts.
- Cross-year/leap-day coverage, shuffled days, duplicates, and incomplete responses.
- Empty today in a current streak; totals and streaks cannot include padding dates.
- XML escaping and preserving spaces in ASCII rows.
- Network failures leave previously generated artifacts intact.

## Task 1: Contribution data

- [x] Write and run failing unittest fixtures for parsing, complete 365-day windows,
  year boundaries, malformed responses, and independently calculated statistics.
- [x] Implement scripts/fetch_contributions.py and shared scripts/common.py.
  Interfaces: parse_contributions(html) -> list[dict];
  build_payload(username, days, end) -> dict; compute_stats(days, end) -> dict.
- [x] Run tests, then fetch live data for sixb5 into data/contributions.json.

## Task 2: Artifacts

- [x] Add profile.json, portrait preparation and row-clipped ASCII SVG generation.
- [x] Generate information card, 53-column heatmap and README from configuration.
- [x] Check XML, 365 dated tiles, padding, escaping, static mode, and image contrast.
  Interfaces: render_heatmap(payload, static=False) -> str;
  image_to_rows(image, columns, rows) -> list[str].
- [x] Generate all artifacts using the public avatar and verify a rendered preview.

## Task 3: Automation and handoff

- [x] Add lean daily workflow and Thai setup/customization instructions, including
  Windows and POSIX commands and optional background removal.
- [x] Run the full tests, live build, deterministic rerender, and browser preview.
- [x] Record exact completed checks and any publishing steps still required.

## Verification record

- Python 3.12: `python -m unittest discover -s tests -v` — 19 passed.
- Live public fetch: 365 days, 2025-10-25 through 2026-10-24, 14 contributions.
- Rebuilding the data and all artifacts twice produced identical SHA-256 hashes.
- XML parsing: all three animated SVGs and three static variants valid.
- Workflow parsed as YAML, with the requested schedule and write permission.
- Browser inspection: all artifacts loaded and settled into readable final frames.
- Independent read-only code review checked 420 calendar windows and reproduced
  the live data. Two important findings (legacy fill levels and dense portrait
  geometry) were reproduced with failing tests, fixed, and verified by the suite.
- Identity choice: use locally authenticated `sixb5`; career details are explicit
  placeholders, and the source image is the account's public identicon.
- Pending external steps: personal photo/details, repository publication, and an
  actual GitHub Actions run. No remote repository was created or modified.
