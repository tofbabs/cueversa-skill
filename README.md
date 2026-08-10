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
`./cueversa.config.json`, `~/.cueversa/config.json`, then a **Drive fallback** —
`cueversa.config.json` in the user's Cueversa Drive folder. `setup` writes both
the local copy and the Drive copy.

**Durability.** On claude.ai a skill's filesystem is per-conversation, so the
durable home for everything Cueversa keeps — config, master CV, and every
application pack — is the user's own **Google Drive** (with the pipeline in
Notion). The sandbox is scratch; each run rehydrates from Drive. This is what
lets a scheduled or next-day run find a setup saved in an earlier session.

The skills never submit applications, never send anything, and are read-only on
job boards.

## Install

**claude.ai / Cowork** — build the archives and upload under Settings → Customize
→ Skills. `package.py` writes both shapes:

```bash
python3 scripts/package.py
# dist/cueversa.skill           <- all four workflows in one skill (upload this)
# dist/cueversa-<skill>.skill   <- the four separately, if you prefer
```

**`cueversa.skill` is the one-upload option** — a single skill that routes by
intent to setup / fetch-jobs / apply-pack / provide-update. Upload it and you have
the whole workflow. The four `cueversa-<skill>.skill` files are the same source
split apart, for anyone who wants them as distinct skills. Both are generated from
the same `plugins/cueversa/skills/` tree, so they never drift.

**Claude Code** — install the plugin from this repo:

```
/plugin marketplace add tofbabs/cueversa-skill
/plugin install cueversa@cueversa-skills
```

## Updating

**Claude Code.** Skills install namespaced from the plugin name, invoked with a
colon: `/cueversa:setup`, `/cueversa:fetch-jobs`, `/cueversa:apply-pack`,
`/cueversa:provide-update` (bare `/setup` also works absent a collision). To pull
a new release:

```
/plugin marketplace update cueversa-skills    # re-pull this repo
/plugin update cueversa@cueversa-skills        # re-fetch if the version changed
```

The marketplace tracks this repo's `main` branch. **The plugin's `version` in
`plugins/cueversa/.claude-plugin/plugin.json` is the cache key** — testers pick
up a change only when that value changes, so intermediate commits are invisible
until you bump it. Updates are user-initiated; there is no silent auto-update
(an org can opt into background checks via `autoUpdate` in
`.claude/settings.json`).

**Release flow (maintainer):** bump `version` in `plugin.json`, commit, push to
`main`, tag (`git tag vX.Y.Z && git push --tags`). Ref-pinning a plugin to a tag
exists but is only needed when a plugin's `source` points at a *separate* repo;
this repo is its own marketplace with a local plugin source, so the `version`
field is the control.

**claude.ai / Cowork.** Uploaded `.skill` archives do **not** sync. Each release,
rebuild `python3 scripts/package.py` and re-upload — one file if you use the
all-in-one `dist/cueversa.skill`, or the four `dist/cueversa-<skill>.skill` files —
replacing the old ones, per account.

## Layout

```
.claude-plugin/marketplace.json      the repo is its own marketplace
plugins/cueversa/
  .claude-plugin/plugin.json
  skills/{setup,fetch-jobs,apply-pack,provide-update}/
scripts/package.py                   builds the .skill archives (four + all-in-one)
scripts/merged/SKILL.md              router for the all-in-one cueversa.skill
spike/                               render-toolchain spike (SPIKE.md)
```

## Design

Full design spec:
`docs/superpowers/specs/2026-08-05-cueversa-skills-repo-design.md` (in the
Cueversa monorepo). The knowledge-graph authoring skill `kg-author` stays private
there, generated from `packages/types`.

Standalone today; when the Cueversa app is reachable, scoring and CV
reconciliation use graph mastery instead of the static skills list.
