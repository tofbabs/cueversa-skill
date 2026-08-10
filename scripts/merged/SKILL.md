---
name: cueversa
description: >-
  The complete Cueversa career workflow in one skill — first-run setup (Notion
  pipeline board, Drive folders, and a curated master CV built through review and
  an evidence interview), sourcing roles into a scored Notion pipeline, building
  submit-ready application packs (tailored ATS-gated CV, cover letter, role brief),
  and logging interview debriefs or hiring-team decisions. Use whenever the user
  wants to set up Cueversa or get started, build/refresh/curate a master CV, run
  the CV interview, fetch or source or score jobs, populate or refresh a job
  pipeline, scan a board, schedule sourcing, prep/pack/tailor applications, work
  the pipeline, make a pack for a role, or log an interview or a rejection/offer
  email — or pastes a job link, JD, or recruiter email. Routes to the right
  workflow by intent. Never submits applications, never sends anything, read-only
  on job boards.
---

# cueversa — the whole career workflow in one skill

This skill bundles four workflows that share one config, one Notion board, and one
Drive. Read the user's intent, resolve the config **once**, then open **exactly
one** file under `workflows/` and follow it to the letter. The workflow file is
authoritative and evolves between releases — do not reconstruct a workflow from
memory, and do not blend two of them.

## Resolve the config first

Every workflow reads the same config, resolved in order: `$CUEVERSA_CONFIG`, then
`./cueversa.config.json`, then `~/.cueversa/config.json`. If none exists, the user
has not set up Cueversa — route to `workflows/setup.md` regardless of what they
asked, because nothing else can run without a board, Drive folders, and a master CV.

## Route

Pick the single workflow that matches the ask:

| If the user… | Open |
|---|---|
| is setting up, connecting tools, or building / refreshing / curating a master CV, or running the CV interview, or configuring searches | `workflows/setup.md` |
| wants to find / source / score roles, populate or refresh the pipeline, scan a board, schedule sourcing, or pastes a job URL to evaluate or add | `workflows/fetch-jobs.md` |
| wants to prep / pack / tailor applications, work the pipeline, make a pack for one role, or pastes a JD or recruiter email to pack | `workflows/apply-pack.md` |
| got an interview transcript (e.g. a Granola export) or a hiring-team email to log, or wants to record an outcome or move a card | `workflows/provide-update.md` |

When the ask is ambiguous between sourcing and packing, prefer the one the user
named a verb for ("find" / "what's out there" → fetch-jobs; "prep" / "tailor" /
"work" → apply-pack). When genuinely unclear, ask one short question rather than
guessing.

## Two workflows in one request

If the user asks for a sequence — "fetch jobs then pack the top 5" — run the
workflows **in order**: complete one fully (including its board writes and its log
step) before starting the next. Do not interleave.

## Telemetry

Each workflow ends with its own "Log the run" step. Honour it once per workflow
run, per the config's `telemetry` block — so a two-workflow request writes two
rows. If the `telemetry` block is absent or disabled, skip it silently.

## What this skill never does

Never submits an application, never sends an email or message, never fills a form
or creates an account, read-only on every job board. It prepares and records; a
human sends. This holds across all four workflows.
