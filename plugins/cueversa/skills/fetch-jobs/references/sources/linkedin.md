# Source recipe: LinkedIn

LinkedIn has no public API for this; harvesting rides the user's own logged-in
browser session via the browser tools. That makes politeness and read-only
behaviour non-negotiable: this is the user's real account.

## Access check (preflight)

Open `https://www.linkedin.com/jobs/` in a browser tab. Logged in looks like
the job-search UI with the user's avatar; logged out looks like a sign-in
wall. If logged out: skip this source, report "LinkedIn: user not logged in -
log in in your browser and re-run". Never enter credentials.

## Running a search

URL pattern (one navigation per query in `profile.searches`):

```
https://www.linkedin.com/jobs/search/?keywords=<url-encoded query>&location=<url-encoded location>&f_TPR=r<seconds>&sortBy=DD
```

- `f_TPR=r604800` = posted in the last 7 days (86400 * profile.posted_within_days)
- `sortBy=DD` = newest first, which surfaces what changed since the last run
- Run each search for each configured location; a "Remote UK"-style location
  string covers remote listings.

Read the result list with the page-text tool. Each card shows title, company,
location, posting age, sometimes comp, and network subtitles.

## Warm-network signals (harvest these - they drive the score)

- Result-card subtitles: "N connections work here" / "N school alumni work
  here" -> `recruiter_warm: true` (soft signal).
- Inside a JD, the "Meet the hiring team" panel naming a 1st or 2nd degree
  connection -> `referral_available: true` (strong signal - a real warm-intro
  path). Never set both from the same signal.
- Surface network-linked roles first in the run report; the warm intro is the
  user's action to take, never the skill's.

## Reading a single job URL (single-URL mode)

A direct link looks like `https://www.linkedin.com/jobs/view/<id>/` (regional
variants like `uk.linkedin.com` are the same job - normalise to the canonical
`www.linkedin.com/jobs/view/<id>/` form for dedupe). Navigate straight to it
and read the detail pane as below; the access check and politeness rules still
apply. If the page shows a login wall, report it rather than working around it.

## Reading a JD

Navigate to the canonical `linkedin.com/jobs/view/<id>/` URL.

**The description and hiring team lazy-load on scroll — you must scroll, then
expand, then read.** Immediately after navigation the left pane shows only the
header card; the "About the job" body and the "Meet the hiring team" panel are
skeleton placeholders until you scroll down to them. Reading the page (either
`get_page_text` or `read_page`) before scrolling returns only the header — which
silently empties `jd_must_haves` and collapses the skills score. A persistent
skeleton is almost always this, not a throttle: **scroll first.**

The reliable sequence:

1. Navigate to the job URL.
2. **Scroll the left pane down** (~3 ticks) so "About the job" and "Meet the
   hiring team" render. A brief pause helps on a slow load.
3. **Click the "… more" toggle** under the description to expand the full text
   (the collapsed view cuts off the requirements list).
4. **Then read** with `get_page_text` — once loaded and expanded it returns the
   whole JD cleanly. (`read_page` also works; page-text is simpler here.)

Extract:

- **must-have skills** — from the requirements / "About you" / "your role"
  lists. Read the actual stack, not the title: a "Senior Backend" title can be a
  Node/TypeScript role, a different fit than the Java the title implies.
- **warm signal** — the "Meet the hiring team" panel (only visible after the
  scroll) names the job poster and their connection degree. A **1st/2nd-degree**
  contact there is `referral_available: true` — the highest-leverage input, so
  never skip the scroll that reveals it.
- **level**, **comp band** if stated,
- **apply channel** — "linkedin-easy-apply" if Easy Apply; otherwise the ATS
  host the "Apply on company website" link points to (a `safety/go?url=`
  redirect — read the real host from it),
- the canonical `linkedin.com/jobs/view/<id>/` URL.

## Politeness and safety

- One tab, sequential navigations, no rapid-fire loops. LinkedIn rate-limits
  and checkpoint-challenges unusual traffic, so pace navigations a second or two
  apart. **A skeleton placeholder is not a throttle — it means you have not
  scrolled the description into view yet (see "Reading a JD"). Scroll first.**
  Only treat it as throttling if the header itself will not render and a
  security checkpoint or CAPTCHA appears — then stop the source and flag
  "Needs manual review".
- If a security checkpoint or CAPTCHA appears: stop the source immediately,
  flag "Needs manual review" in the run report, and move on. Never attempt to
  bypass it.
- Read-only: never click Apply, Save, Follow, Connect, or Message. Never
  dismiss/report listings.
- The account belongs to the user; anything that changes account state is out
  of bounds.
