# Queue rules (bulk mode)

How to turn the board's `Identified` layer into a queue of roles worth packing.
Read this when running bulk mode. Direct mode skips straight to the pack.

The cueversa config is canonical for the board id, statuses and thresholds. This
file is only the selection algorithm layered on top.

## The governing principle: the queue must clear itself

Every card you look at either gets packed or gets moved out of `Identified` with
a written reason. Nothing is left frozen for the next run to trip over again.

This matters more than it sounds. The failure mode: a run demotes cards, writes
the reason into `Notes`, but the `Status` write does not land — the cards sit at
`Identified` carrying notes that say "moved to Backlog", and every later run
re-examines the same roles and produces nothing. **After writing demotions,
re-query the board and confirm the `Status` values actually changed.** A `Notes`
line is not a demotion. A run that ends short must be because `Identified`
genuinely ran out, not because cards were skipped in place.

## Step 1: Build the queue

Query `Status = 'Identified'` ordered by `Fit Score` desc. Also pull every card
in an ACTIVE status (`Identified`, `Ready to Apply`, `Applied`, `Recruiter Call`,
`Interview`, `Offer`) so the company-conflict check needs no second round trip.

Two filtering notes that are easy to get wrong:

- **`Missing tailored CV` and `Needs manual review` do NOT exclude a card** —
  hints, not gates. Treat them as context for the pack.
- **`Application blocked` and `External registration required` DO exclude** —
  they need a human decision or an account this skill may not create. Leave them
  in place and list them in the report. They are the one legitimate reason a card
  stays at `Identified`.

Exclude the non-job `CONVERSION DASHBOARD` card.

## Step 2: De-duplicate by company, before doing any work

Do this before opening a single JD — tailoring a CV for a role you're about to
park is pure waste.

- **Active-card conflicts.** If a company already has an `Applied`,
  `Recruiter Call`, `Interview` or `Offer` card, do not pack any `Identified`
  card for that company. Move those to `Backlog` with a `Notes` line naming the
  active card that blocks them. Two live applications at one employer is exactly
  what the one-best-fit rule exists to prevent, and can cost the candidate both.
- **Sibling collapse.** Where several `Identified` cards share a company, keep the
  highest `Fit Score` and move the rest to `Backlog`, naming the chosen role.
  Pick automatically; do not hold siblings for a human decision.
- **Agencies are never collapsed.** Where the real end employer is hidden and
  differs per role (Oliver Bernard, Hunter Bond, Primis, Saragossa, Robert
  Walters, Selby Jennings and similar), set `employer_key = null`. Two roles from
  one agency are usually two different end clients.

When you park a card, write the revival condition into `Notes`: which active card
blocks it, and that it should be revived if that card closes. A demotion without
a revival condition is a deletion with extra steps.

## Step 3: Verify live and re-confirm the score, per role

Open the `JD URL` read-only and confirm the listing is real and still open.

**Reading a LinkedIn JD — use the guest endpoint, not the browser.** On
`linkedin.com/jobs/view/<id>` the description body is often not served to the
page. The guest endpoint serves the full description as plain text:

```
https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/<jobId>
```

It also returns pay range, posting age, applicant count, seniority, and whether
it says **"No longer accepting applications"** — check that line first. This is
faster and more reliable than the browser scroll-and-read, and avoids the
throttle; only fall back to the browser when no clean text source exists.

Then refresh the parsed job dict and re-run `../fetch-jobs/scripts/score.py`.
Scores drift because the card was created from a search snippet and the real JD
is richer — treat the stored `Fit Score` as provisional until you've read the
spec.

Three outcomes send a card out of the queue:

| What you found | What to do |
|---|---|
| Closed / expired / "No longer accepting applications" | `Backlog`, flag `Application blocked`, `Notes` with today's date, what the page said, and anything salvageable (rate, stack, a direct-approach angle) |
| URL doesn't resolve to a specific listing (careers homepage, keyword search, login wall) | Same treatment — an unverifiable card can't be scored or tailored honestly |
| Rescores below `thresholds.backlog_min` | `Backlog` with the rescore reason and the new number |

Keep pulling replacements until the requested count is packed or `Identified` is
exhausted. There's no cap on how many cards you may clear while filling slots.

## Step 4: Report in three parts

A run report that only lists successes hides the work that matters most.

1. **Ready to Apply** — each role with ATS score and weighted coverage, Fit
   Score, apply channel, one line on how to submit, and any honest gap worth
   knowing before sending.
2. **Moved out of Identified** — every card demoted or blocked this run, one line
   each, grouped: dead listing / rescored below floor / company conflict.
3. **Roles worth a manual approach** — any dead listing or parked card that was a
   genuinely strong match, where contacting the company or agency directly, or
   closing a stale active application, is the sensible next move. This is where
   the run earns its keep: a 9.7 parked behind a silent 8.6 is something the user
   can act on today.
