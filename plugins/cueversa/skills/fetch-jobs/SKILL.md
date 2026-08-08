---
name: fetch-jobs
description: >-
  Source new job roles from configured job boards (LinkedIn first, extensible to
  Indeed, Otta, Welcome to the Jungle and others) into a Notion job pipeline
  board, scoring each role against the user's profile with a deterministic Fit
  Score. Use this skill whenever the user wants to fetch jobs, source roles,
  scan LinkedIn or any job board for openings, refresh or seed a job pipeline,
  set up automated job sourcing, or schedule a recurring job search - even if
  they do not name a specific board. Also trigger on "find me roles", "what new
  jobs are out there", "populate my job board", when setting up a scheduled
  job-sourcing task, or when the user pastes a URL to a specific job posting
  and wants it evaluated or added to their pipeline ("what about this role",
  "add this job", "score this listing"). First run performs guided setup
  (profile interview, board creation); later runs are fully autonomous and
  schedule-safe.
---

# fetch-jobs: source roles into a Notion pipeline

One clean pass, safe to run on a schedule: verify prerequisites, harvest fresh
listings from each enabled source, normalise, dedupe, score, and add the best
new roles to the user's Notion Job Pipeline board. Idempotent by design - a
re-run must never create duplicate cards.

Two modes, sharing every phase below:

- **Search mode** (default): run the configured searches across enabled
  sources. This is the scheduled path.
- **Single-URL mode**: the user supplies one or more specific job URLs. Skip
  Phase 2's searches and treat each URL as the harvest set - everything else
  (preflight, dedupe, scoring, card creation, report) applies unchanged. See
  "Single-URL mode" below.

## Phase 0: Preflight gate

Two checks must pass before any sourcing happens. On a scheduled
(non-interactive) run, a failed check ends the run with a clear report of what
is missing - never guess or half-run.

### 0a. Setup precondition — refer, don't improvise

Resolve the config in order: `$CUEVERSA_CONFIG`, then `./cueversa.config.json`,
then `~/.cueversa/config.json`. Setup is **present** when that config exists and
carries both a resolved Notion board (`identity.notion.job_board.data_source_id`)
and a non-empty `profile.searches`. If so, load it and go to 0b.

**If setup is absent or incomplete, do not run a setup interview here — that is
`cueversa:setup`'s job.** Sourcing needs a curated master CV and derived searches
that this skill does not produce.

- **Interactive run:** stop and refer the user to setup — "You need to run
  `cueversa:setup` first: it curates your master CV, creates your Notion board
  and Drive folders, and derives the roles to search. Shall I start it?" Offer to
  hand off; do not collect profile answers yourself.
- **Scheduled run:** end the run with a one-line report naming the missing piece
  (`no config` / `no board` / `no searches`) and that setup must be run once,
  interactively. Never half-run.

The board itself is created by `cueversa:setup`, so a complete config already
carries its ids; this skill only confirms the board is alive, never creates one.

### 0b. Job board access

For each source in `run.sources`, verify access before harvesting. Each source
has a recipe file under `references/sources/` - read the recipe for every
enabled source. For LinkedIn (`references/sources/linkedin.md`): the user must
already be logged in to LinkedIn in their browser. Open a browser tab, load
`https://www.linkedin.com/jobs/`, and confirm a logged-in state (job search UI
visible rather than a sign-in wall). If a login wall or security checkpoint
appears: stop that source, tell the user to log in themselves, and never touch
credentials or attempt to bypass a checkpoint - the skill is strictly read-only
on every job board.

### 0c. Notion board is alive

Fetch `identity.notion.job_board.data_source_id` to confirm the board still
exists and load its live schema. If the fetch fails (board deleted or moved),
treat it as an incomplete setup per 0a and refer the user back to
`cueversa:setup` rather than recreating the board here.

## Phase 1: Load board state

Query the data source for every existing card's Role, Company, Status, and JD
URL (paginate; exclude any non-job utility cards such as a metrics dashboard).
Build:

- a **dedupe key set**: normalised `company|role` plus JD URL host+path, for
  cards in ANY status - a role that was ever tracked never comes back;
- the set of **active employer keys** - employers with a card in Identified,
  Ready to Apply, Applied, Recruiter Call, Interview, or Offer. Backlog and
  Closed are not active.

## Phase 2: Harvest

For each enabled source, follow its recipe file to run every query in
`profile.searches` with the config's location and freshness filters
(`posted_within_days`). Capture per listing: title, company, location, type
(perm/contract), posting age, comp if shown, must-have skills from the JD, the
canonical job URL, apply channel, and any warm-network signals the source
exposes (e.g. LinkedIn's "N connections work here" or a connection on the
hiring team).

Prioritise network-linked listings first when the source surfaces them - a
warm path is the highest-leverage signal in the score.

Stop harvesting once `max_new_cards_per_run` genuinely new candidates (i.e.
not already on the board) have been collected, or the searches are exhausted.
Be gentle: few tabs, pauses between navigations, and stop a source entirely if
it challenges the session.

## Phase 3: Normalise, dedupe, score

Normalise each listing to the scorer's input shape (see the scorer docstring).
Map network signals conservatively: a 1st/2nd-degree connection on the hiring
team means `referral_available: true`; a connection merely at the company means
`recruiter_warm: true`; never both from one signal.

Drop anything whose dedupe key already exists. Collapse near-duplicates within
the run (same role at the same company via two channels) keeping the
direct-ATS version.

Score deterministically with the bundled scorer:

```bash
python3 scripts/score.py --config "$CUEVERSA_CONFIG" < jobs.json   # or the resolved cueversa.config.json path
```

Apply thresholds from config (defaults: >= 8.0 Identified, 5.0-7.9 Backlog,
< 5.0 no card - just list it in the report so nothing silently vanishes).

Then enforce **one best-fit per company**: the scorer's `best_per_company`
annotation keeps only the highest-scoring role per direct employer and parks
the rest. Agency listings with a hidden end-client get `employer_key: null`
and are never collapsed together. Never create a second active card for an
employer that already has one - park it as Backlog with a note naming the
existing card.

## Phase 4: Create cards

Create one page per kept role under the data source with: Role, Company,
Status (Identified or Backlog), Type, Location, Tech Stack, Comp (est.), Fit
Score, JD URL, Notes (one-line fit/gap summary from the scorer flags, naming
the network tier if warm), and Application Flags = ["Missing tailored CV"].
Leave Date Applied, CV Variant, and ATS Score blank - they belong to the
application step, not sourcing.

Every new Identified card also gets, in the page body:

- `## Research` - what the company does, role reality, comp benchmark,
  interview process as far as the JD reveals it;
- `## Recommended conversion strategy` - the single strongest proof point from
  the user's profile to lead with for this role.

Keep board writing plain and human: short sentences, no filler, no em dashes.

## Single-URL mode

When the user gives a direct link to a job posting instead of asking for a
sweep:

1. **Preflight still applies**, but scoped: config must exist (else refer to
   `cueversa:setup` per Phase 0a), the Notion board must resolve, and only the
   source that owns the URL needs an access check. Identify the source from the URL host (e.g.
   `linkedin.com/jobs/view/...` -> the LinkedIn recipe; an ATS host like
   Greenhouse/Ashby/Lever can be fetched directly as a web page). If no recipe
   matches, fetch the page and parse the JD from the raw content - a recipe is
   a convenience, not a requirement, for a single known URL.
2. **Dedupe first.** If the URL or the normalised company|role already has a
   card, do not create another - link the existing card and report its status
   instead.
3. **Read the JD fully** and normalise exactly as in Phase 3, including any
   warm-network signals the page shows.
4. **Score with the bundled scorer.** The per-run cap does not apply - the
   user asked for this specific role.
5. **Always create a card for a non-duplicate** (the user's explicit interest
   overrides the drop threshold): place it by the normal thresholds, but if it
   scores below `thresholds.backlog_min`, create it as Backlog with a
   "Needs manual review" flag and be direct in the Notes about why the score
   is low. If the role's employer already has an active card, park the new one
   as Backlog with a note naming the existing card, per the usual rule.
6. **Report** the score breakdown, the flags, the placement decision, and the
   card link. This mode is usually interactive, so a short conversational
   summary beats the full sweep report.

## Phase 5: Report

End with a concise summary: N searched per source, N added (with Fit Scores),
N deduped, N parked (naming what each lost to), N dropped below threshold, any
sources skipped at preflight and why, and the current top 5 Identified by Fit
Score. Link the board. On scheduled runs this report is the primary output.

## Guardrails

- **Read-only on every job board.** This skill never applies, never messages,
  never accepts terms, never handles credentials, never bypasses a checkpoint.
- **Idempotent.** Re-running must not duplicate cards or double-add a company.
- **Autonomous when scheduled.** No questions mid-run; make the reasonable
  choice and note it in the report. The only interactive moment is first-run
  setup.
- **Config is canonical.** Board ids, thresholds, caps, and the profile all
  come from the resolved `cueversa.config.json` (written by `cueversa:setup`) -
  never hardcode them.

## Extending to a new source

Add a recipe file at `references/sources/<source>.md` describing: how to
verify access, how to run a search with the config's filters, how to read a
listing (fields + any warm-signal indicators), and any politeness rules. Then
add the source name to `run.sources`. Phases 1 and 3-5 are source-agnostic and
need no changes. Prefer an API or MCP connector over browser automation when
one exists for the source.
