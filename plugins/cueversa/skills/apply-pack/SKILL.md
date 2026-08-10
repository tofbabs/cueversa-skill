---
name: apply-pack
description: >-
  Build submit-ready job application packs — in bulk from the top of the Notion
  pipeline board, or for one role from a job link, pasted JD, or a card. Each pack
  is a numbered Career/NNN_Company_Role folder with the JD verbatim, an ATS-gated
  CV tailored from the master CV (rendered to txt/docx/pdf), a cover letter, a
  recruiter reply when there's a named recruiter, and a role brief — then sets the
  board card to Ready to Apply. Use whenever the user wants to prep, pack, tailor
  or work applications ("prep the top 5", "work my pipeline", "make a pack for this
  role", "tailor my CV for this job", "what should I apply to next"), or pastes a
  job link, JD or recruiter email. Never submits — it prepares; a human sends.
---

# apply-pack — submit-ready packs from the pipeline

Two ways in, one thing out: a folder the user can submit from without reworking
it. **Bulk mode** drains the top of the board; **direct mode** takes one role
from a link, pasted JD, recruiter email, or a card. Both produce the same depth
and both stop at `Ready to Apply`.

> **This skill never submits.** No form fills, no account creation, no recruiter
> emails sent, no LinkedIn messages, no CAPTCHA handling. Submitting is the
> user's step — the whole point of stopping at Ready to Apply is that they read
> what goes out under their name.

## Phase 0: Preconditions

Resolve the config in order: `$CUEVERSA_CONFIG`, `./cueversa.config.json`,
`~/.cueversa/config.json`, then the **Drive fallback** — search the user's Google
Drive for `cueversa.config.json` (setup saves it in the Cueversa root folder). On
claude.ai the sandbox filesystem is per-conversation, so a scheduled or next-day
run finds nothing local and **must** fall back to Drive; download it to
`~/.cueversa/config.json` and use that path as `$CUEVERSA_CONFIG` for the scripts.
Setup is complete when the resolved config carries the Notion board
(`identity.notion.job_board.data_source_id`), the Drive `packs/` folder, and a
**master CV** (`identity.drive.master_cv_file_id`, or a local
`~/.cueversa/master-cv.json`). If any is missing, refer the user to
`cueversa:setup` and stop — the master CV rules and board contract live there,
and guessing produces confident, wrong output. Everything downstream reads its
board id, thresholds and master CV from the config; nothing here is hardcoded.

## Phase 1: Pick the mode

**Direct mode** — the user gives a specific role: a URL, a pasted JD, a recruiter
email, a company + title, or names a card already on the board.

**Bulk mode** — "the top N", "the pipeline", "the best roles", or no specific
role. Default N is `run.max_new_cards_per_run` (or 5). Honour a stated number.

Bulk mode runs the queue in `references/queue_rules.md` first — the selection
algorithm, the company-conflict check, and the rule that **every card touched is
either packed or moved out of `Identified` with a written reason** (and the
status write is verified, not just noted). Direct mode skips straight to the pack.

## Phase 2: Read the JD properly

Never work from a search snippet — a stored Fit Score derived from one is
provisional until you've read the real spec. Save the JD **verbatim** into the
pack; the ATS scorer and role brief both parse it, so a paraphrase degrades the
run.

**LinkedIn: use the guest endpoint, not the browser.** `linkedin.com/jobs/view/<id>`
lazy-loads the body and often serves nothing to a reader. The guest endpoint
returns the full description as plain text, plus pay range, posting age,
applicant count and whether it says **"No longer accepting applications"**:

```
https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/<jobId>
```

Check the closed line first; if dead, say so and don't build a pack (offer the
direct-approach angle instead). For ATS hosts (Greenhouse, Ashby, Lever,
Workday, SmartRecruiters) fetch the page directly. Only fall back to the browser
scroll-and-read (`references/sources/linkedin.md` in `fetch-jobs`) when no clean
text source exists.

## Phase 3: Score the role (Fit)

Parse the JD into the scorer's input shape and run the cueversa Fit scorer:

```bash
python3 ../fetch-jobs/scripts/score.py --config "$CUEVERSA_CONFIG" < job.json
```

The Fit band is context for prioritising, not a gate. In **bulk mode** a role
below `thresholds.backlog_min` goes to `Backlog`, not into a pack. In **direct
mode** the user asked for this specific role — build the pack, and put the low
score and the reason at the top of the role brief. Refusing to pack what they
asked for is unhelpful; letting them submit blind to a 6.2 is worse.

## Phase 4: Build the pack

Read `references/pack_spec.md` for the file list, CV tailoring rules, the ATS
gate, and the role-brief structure. The essentials:

**Folder.** `Career/NNN_Company_Role/` under the Drive `packs/` folder, using the
next free NNN derived from the board — `max(NNN in existing Folder values) + 1`,
never a stored counter. Company is the **end client** where known; for agency
listings with a hidden client, use the agency name and record the hidden-client
fact in the brief.

**Tailor the CV from the master.** Read the master CV (never edit it) — a local
`~/.cueversa/master-cv.json` if present, otherwise pull it from Drive by
`identity.drive.master_cv_file_id`; on claude.ai it always comes from Drive. Author
a tailored `<candidate>-<company>-cv.md`:

- **Brevity beats coverage.** Drop everything the JD doesn't ask for, whole
  engagements included. A focused two-page CV beats a 100%-coverage three-pager
  in a six-second screen.
- **Lead with the identity the JD wants** in the headline and first summary line.
- **Reframe by role type** — Java perm role → lead the Java backend identity;
  AI/product role → lead the AI systems work. Same facts, different ordering.
- **Never fabricate** a skill, tool, year or contact detail to clear a scorer.
- **No em dashes** anywhere (en dashes in date ranges are fine).

Render it to the pack's fixed shape:

```bash
python3 scripts/render_cv.py <candidate>-<company>-cv.md
```

That emits `.txt`, `.docx` and `.pdf` from the canonical `.md` to one consistent
template. The `.md` is canonical — never hand-edit the rendered files; edit the
`.md` and re-render.

**ATS gate.** Score the rendered text against the JD:

```bash
python3 scripts/ats_weighted.py --cv <candidate>-<company>-cv.txt \
    --jd jd.txt --title "<Company> <Role>" --report ATS_Report.txt
```

It parses terms from the JD and weights them (3.0 essential/responsibilities,
1.5 body, 1.0 desirable). **Gate: weighted coverage ≥ 0.85 and zero formatting
blockers. Iterate the CV, not the scorer.** Two honest-failure cases: a term
missing because the skill isn't real stays missing with an integrity note; a
blocker that can't be cleared truthfully is recorded, never faked.

**Cover letter, recruiter reply, role brief.** A formal `cover-letter.md`; a
`Reply_Email_<Company>_<Recruiter>.md` (with a "Before you send" checklist) only
when there's a named recruiter or agency approach; and `Role_Brief.md` — the
main working document, structure in `pack_spec.md`. Research the end client and
supplier first (Companies House for agencies), and run the same-end-client
collision check.

**`pack.json`** binds the folder to the board: the Notion page id and the NNN.

## Phase 5: Update the board

One card per role — never a duplicate; update the existing card. Packed roles
get `Status = Ready to Apply`, plus `CV Variant`, `ATS Score`, `Folder`, and a
`Notes` line carrying the fresh Fit Score and band, weighted ATS coverage, apply
channel, and the honest gaps. Leave `Application Flags` empty and **do not set
`Date Applied`** — the user owns the move to `Applied`. In direct mode, if the
role has no card, create one with the `## Research` and `## Recommended
conversion strategy` body sections. A role that can't be packed truthfully (needs
a clearance, an account, or a payment) stays at `Identified`, flagged
`Needs manual review` or `External registration required` with the reason.

## Phase 6: Report

**Bulk** uses the three-part report (`queue_rules.md`): what's Ready, what moved
out of `Identified` and why, and roles worth a manual approach — that third part
usually earns the run. **Direct** is shorter: ATS score and weighted coverage,
Fit Score, the single honest gap, any collision risk, the rate anchor, and the
one action to take first. Present the tailored CV and master CV as files; cite
the board URL.

## Guardrails

- **Never submits.** Stops at Ready to Apply, every time.
- **Never fabricates.** Not a skill, a year, or a phone number. Qualified claims
  get an integrity note.
- **Master reconciliation.** A genuinely real skill a JD forces into the CV that
  the master lacks gets written back to `master-cv.json` in the same pass, or the
  master rots and every future pack starts further behind.
- **The `.md` is canonical.** Never hand-edit the `.docx`/`.pdf`.
- **No em dashes** anywhere — CV, cover letter, emails, brief, board text.
- **One card per role, one active application per end client.**
- **Flag, don't decide, on money.** Give the anchor, landing and floor; note IR35
  and tax mechanics are general information, not advice.
- **Money or registration walls** leave the card at `Identified`, flagged.

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
