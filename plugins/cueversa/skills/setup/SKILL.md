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
Cueversa root, `cv/`, and `packs/`. Record every id in the config's `identity`.

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

## Phase 3 — derive role fit

Populate `profile.skills` and propose `profile.searches` from the master CV;
show them for editing before writing. When Cueversa is reachable, additionally
reconcile against graph mastery, and say plainly when that was skipped.

## Idempotent

Re-running detects an existing config and master CV and updates only what
changed.
