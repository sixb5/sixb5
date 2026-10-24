# Terminal profile art

Implement the supplied Python + repository-owned SVG approach: a monochrome
ASCII avatar, a Neofetch information card, a real 53-column contribution calendar,
and a centered GitHub README. Animations play once and finish in a readable state.

The workspace is empty. The locally authenticated GitHub account is `sixb5`;
use it as a configurable starting point, not the tutorial author's identity.
Use the account's public avatar until a personal source photo is supplied. Personal
career details must remain explicit placeholders rather than invented claims.

`profile.json` owns identity, information rows, and portrait settings. Independent
Python command-line scripts produce the three exact SVG filenames requested.
Runtime paths resolve from the project, not the caller's working directory.
`STATIC=1` removes animations. Reduced-motion viewers get the final frame.

Daily jobs install only requests and BeautifulSoup. Pillow, NumPy, OpenCV and
optional rembg belong to local photo preparation. No tokens, remote widgets,
JavaScript, or externally loaded SVG resources are required.

Fetch each intersecting calendar year separately: GitHub's HTML endpoint returned
an entire calendar year even for a cross-year request during inspection. Merge by
ISO date and select the last 365 dates through the UTC day. Missing/ambiguous
counts fail before replacing the previous JSON; future/padding days are not data.
Current streak permits an unfinished empty today, longest streak is scoped to the
displayed interval, and monthly totals are partial at the interval boundaries.

The workflow refreshes only JSON and heatmap at 06:17 UTC, on relevant pushes to
main, and manually. It grants contents:write and commits only changed artifacts
with [skip ci]. Local generation and review are in scope; publishing the user's
public profile remains a separate action.

Alternatives: GraphQL needs credentials; hosted widgets add a remote renderer.
The supplied HTML/SVG approach meets the no-token, self-hosted-artifact constraint.
