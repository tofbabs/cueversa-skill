# Notion Job Pipeline board - creation and schema spec

When no board exists (config `notion.data_source_id` is null and no database
titled `notion.board_name` is found), create one with exactly this schema.
Property order matters - create them in the order listed so views read
naturally left to right.

## Properties (exact names, types, and options, in order)

| # | Property | Type | Options / notes |
|---|---|---|---|
| 1 | `Role` | title | Job title. The page title. |
| 2 | `Company` | text | Actual employer, or "X (agency, end client hidden)" |
| 3 | `Status` | select | Identified, Backlog, Ready to Apply, Applied, Recruiter Call, Interview, Offer, Closed |
| 4 | `Type` | select | Perm, Contract, FTE, Contractor |
| 5 | `Location` | text | e.g. "London (Hybrid)", "Remote UK" |
| 6 | `Tech Stack` | multi-select | Seed with the user's `profile.skills` (title-cased) plus common infra terms; add options as JDs demand |
| 7 | `Fit Score` | number | 0-10 from scripts/score.py. Sort the board on this, descending. |
| 8 | `ATS Score` | number | 0-100 keyword coverage, set by the CV-tailoring step (not by sourcing) |
| 9 | `Comp (est.)` | text | Free text, e.g. "GBP110-130k" or "GBP600/day inside IR35" |
| 10 | `JD URL` | url | Canonical listing link |
| 11 | `CV Variant` | url | Link/path to the tailored CV used (not set by sourcing) |
| 12 | `Folder` | text | Local pack folder, if the user keeps per-role folders |
| 13 | `Recruiter / HM` | text | |
| 14 | `Follow-up Plan` | text | CHANNEL / CONTEXT / ACTION / WATCH, one per line (set at apply time) |
| 15 | `Next Follow-up` | date | |
| 16 | `Last Touch` | date | |
| 17 | `Date Applied` | date | Set when Status becomes Applied (not by sourcing) |
| 18 | `Notes` | text | One-line fit/gap summary |
| 19 | `Application Flags` | multi-select | Missing tailored CV, Application blocked, External registration required, Needs manual review, Submitted |

## Status lifecycle

```
Backlog / Identified -> Ready to Apply -> Applied -> Recruiter Call -> Interview -> Offer -> Closed
```

- `Identified` - live candidate role worth pursuing. Entry rule: Fit Score >= the
  `thresholds.identified` value (default 8.0).
- `Backlog` - sourced but not a priority now (below threshold, or parked by the
  one-best-fit-per-company rule).
- Sourcing runs only ever create Identified/Backlog cards and only ever
  re-touch Identified/Backlog cards. Ready to Apply and beyond belong to the
  human and to application workflows - never modify them from sourcing.

## After creating

Fetch the new database to obtain its data source id, then write
`database_id`, `data_source_id`, and `board_url` back into
`fetch-jobs.config.json` so every later run resolves the board instantly.

Add a default view sorted by `Fit Score` descending if view creation is
available; otherwise tell the user to sort the board on Fit Score once.

## Reading an existing board

Prefer SQL-mode data source queries, name the columns you need (a bare
SELECT * over a big board can blow the token budget), paginate with
LIMIT/OFFSET, and exclude any non-job utility card (e.g. a dashboard row) from
dedupe and scoring.
