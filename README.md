# cueversa-skills

A standalone family of Claude skills that take a job seeker from a curated master
CV to a worked application pipeline — on their own Notion, Google Drive, and
Claude subscription. No server, no account, nothing proprietary.

Four skills, divided by how they run:

| Skill | What it does | Mode |
|---|---|---|
| **setup** | Establishes the Notion board + Drive folders, curates a reviewable master CV (parse → review + add entries → evidence interview), and derives the skills and searches everything else uses | interactive, first-run |
| **fetch-jobs** | Sources roles from job boards into the Notion pipeline, scored against the master CV with a deterministic Fit Score | autonomous / scheduler-safe |
| **apply-pack** | Builds submit-ready packs — tailored CV (ATS-gated), cover letter, role brief — in bulk or for one role, and moves the card to Ready to Apply | autonomous / scheduler-safe |
| **provide-update** | Logs an outcome (hiring-team email or interview transcript) and moves the card | interactive intake |

Everything reads one config file, resolved in order: `$CUEVERSA_CONFIG`,
`./cueversa.config.json`, `~/.cueversa/config.json`. `setup` writes it. The
skills never submit applications, never send anything, and are read-only on job
boards.

## Install

**claude.ai / Cowork** — build the flat archives and upload each under
Settings → Customize → Skills:

```bash
python3 scripts/package.py   # writes dist/cueversa-<skill>.skill
```

**Claude Code** — install the plugin from this repo:

```
/plugin marketplace add tofbabs/cueversa-skill
/plugin install cueversa@cueversa-skills
```

## Layout

```
.claude-plugin/marketplace.json      the repo is its own marketplace
plugins/cueversa/
  .claude-plugin/plugin.json
  skills/{setup,fetch-jobs,apply-pack,provide-update}/
scripts/package.py                   builds the flat .skill archives
spike/                               render-toolchain spike (SPIKE.md)
```

## Design

Full design spec:
`docs/superpowers/specs/2026-08-05-cueversa-skills-repo-design.md` (in the
Cueversa monorepo). The knowledge-graph authoring skill `kg-author` stays private
there, generated from `packages/types`.

Standalone today; when the Cueversa app is reachable, scoring and CV
reconciliation use graph mastery instead of the static skills list.
