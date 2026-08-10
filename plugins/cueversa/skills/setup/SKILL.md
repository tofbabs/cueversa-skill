---
name: setup
description: >-
  Guided first-run setup for the Cueversa career workflow. Establishes the
  user's Notion job-pipeline board and Drive folders, curates a master CV from an
  existing CV (parse, then an evidence interview that fills gaps and quantifies
  bullets), saves it to Drive as structured JSON plus a rendered document, and
  derives the skills and target searches the sourcing step will use. Use this
  skill when the user wants to set up Cueversa, get started, connect their job
  search, build or refresh a master CV, curate a CV, run the CV interview, or
  configure job sourcing. Re-runnable: on an existing setup it updates only the
  piece that changed. Never scores or grades the CV, and never sends anything.
---

# setup — establish integrations, curate the master CV, derive role fit

> Skeleton. Full contract in
> `docs/superpowers/specs/2026-08-05-cueversa-skills-repo-design.md` §6.1.

Three concerns, one first-run flow, because they are sequential: you do not
configure without curating, and you do not curate without deriving fit.

## Phase 1 — establish integrations

Resolve or create the Notion board (lazily: check config, else find by name,
else create from the board schema). Resolve or create the Drive folders — a
Cueversa root, `cv/`, and `packs/`. Record every id in the config's `identity`
(shape in `assets/config.template.json`: `identity.notion.job_board` and
`identity.drive`).

## Where your data lives — Drive is the durable home

**On claude.ai the sandbox filesystem is per-conversation**: `~/.cueversa/` and any
working file vanish when the chat ends or a scheduled run finishes. So the rule is
absolute — **anything that must outlive a session lives in the user's own Google
Drive (or Notion), and the sandbox is scratch only.** Every run rehydrates what it
needs from Drive; nothing durable is trusted to the local filesystem alone.

Three things persist, all under the Cueversa Drive folder:

- **Config** — `cueversa.config.json` in the Cueversa **root** folder. Setup writes
  it here (recording `identity.drive.config_file_id`) and also to
  `~/.cueversa/config.json` for the session and for Claude Code, where the local
  home persists on its own. Drive is the source of truth.
- **Master CV** — `master-cv.json` in the `cv/` folder (`master_cv_file_id`),
  rendered document beside it. Already durable; see 2e.
- **Application packs** — each `Career/NNN_…` folder in the `packs/` folder.
  `cueversa:apply-pack` writes packs straight to Drive. Already durable.

Config resolves in order: `$CUEVERSA_CONFIG`, `./cueversa.config.json`,
`~/.cueversa/config.json`, then the **Drive fallback** — search Drive for
`cueversa.config.json`. Every other skill's preflight reads this same order and,
finding nothing local, pulls the config from Drive — that is what makes a next-day
or scheduled `cueversa:fetch-jobs` / `cueversa:apply-pack` find the setup you
saved. Re-running setup rewrites both copies.

## Phase 2 — curate the master CV

The master CV is the canonical record of what the user has *done*. It is built
**with** the user, not parsed and accepted: they review every entry and can add
entries that were never in the source. The structure is
`assets/master-cv.template.json` — every entry (role, bullet, skill, evidence)
carries an `id`, so it can be shown, edited, or appended to precisely.

### 2a. Ingest the source

Accept a CV from Drive (a file in the `cv/` folder or one the user names), a
local path, or pasted text. If none is given, offer to start from an empty
master CV and build it up through review — the source is a convenience, not a
requirement.

### 2b. Parse into the schema

Fill `master-cv.template.json`: candidate header, summary, experience (roles,
each with dated bullets), skills, education. Mark each bullet's `confidence`
(`clean` / `check` / `partial`) and raise `flags` for gaps, unparsed structures,
and bullets with no metric. **Never score or grade the CV** — parsed, not judged.

### 2c. Review, and introduce new entries — the load-bearing step

Walk the user through the draft section by section and let them steer. At each
section they can:

- **confirm** an entry as-is,
- **edit** any field (fix a title, a date, reword a bullet, add a metric),
- **introduce a new entry** that the source CV never had — a role, a bullet, a
  skill, or a standalone evidence point. New entries get a fresh `id` and
  `source: "manual"`.
- **remove** an entry that does not belong.

Show a rendered view (via `scripts/render_cv.py` on the current draft) whenever
the user wants to see it as a document rather than as fields. Every change is
the user's; apply it to the JSON and reflect it back. Do not silently rewrite
prose the user wrote.

### 2d. Evidence interview

For the flags from 2b — unquantified bullets first, then claimed-but-unevidenced
skills, then omissions — ask targeted questions. Capture answers as `evidence`
entries (`impact` / `depth` / `leadership` / `quantified` / `hidden`), and fold
accepted ones into the relevant bullet or skill behind the same review step as
2c. This is where "what do people ask you for that isn't on your CV" becomes a
new entry.

### 2e. Save

Write `master-cv.json` (canonical) to the Drive `cv/` folder, render the
document beside it with `scripts/render_cv.py`, and record `master_cv_file_id`
in the config. The rendered copy is generated from the JSON and never edited in
place — edit the JSON and re-render, or the two drift apart.

Then persist the config itself, per **Where your data lives**: write
`cueversa.config.json` to the Cueversa Drive root (recording
`identity.drive.config_file_id`) and `~/.cueversa/config.json` locally. Without
the Drive copy, a claude.ai tester's setup is gone the moment the chat ends.

## Phase 3 — derive role fit

Populate `profile.skills` and propose `profile.searches` from the master CV;
show them for editing before writing. When Cueversa is reachable, additionally
reconcile against graph mastery, and say plainly when that was skipped.

## Idempotent

Re-running detects an existing config and master CV and updates only what
changed. From a fresh claude.ai session it first pulls `cueversa.config.json`
from Drive (per **Where your data lives**), so a re-run updates the saved setup
rather than starting over.

## Log the run (beta telemetry)

If the config has `telemetry.enabled: true` and a `telemetry.activity_data_source_id`,
append **one row** to that Notion data source at the very end of the run:

- **Event** — short label, e.g. `fetch-jobs · 5 sourced` or `apply-pack · Conduct`
- **Tester** — `telemetry.tester`
- **Skill** — this skill's name
- **Count** — roles sourced / packs built / cards updated (a number)
- **Outcome** — one line
- **Workspace** — `identity.notion.workspace_name`

This is the shared beta activity log. It records **that** the skill ran and a
one-line result — never CV contents, JD text, or personal data. If the
`telemetry` block is absent or `enabled` is false, skip it silently.
