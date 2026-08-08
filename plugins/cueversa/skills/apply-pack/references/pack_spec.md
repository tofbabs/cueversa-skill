# Pack specification

What a finished pack contains and the standard each file is held to. Same depth
in bulk and direct mode. A pack the user has to rework before sending has not
saved them anything.

## Folder

`Career/NNN_Company_Role/` under the Drive `packs/` folder, using the next free
NNN. Derive it from the board — the largest number in existing `Folder` values,
plus one; never a stored counter. Company is the **end client** where known; for
agency listings with a hidden client, use the agency name and record the
hidden-client fact in the role brief.

## Files

| File | Contents |
| --- | --- |
| `jd.txt` | The spec verbatim, plus source URL, recruiter, date received, and the verification line (date checked, posting age, applicant count, open/closed) |
| `<candidate>-<company>-cv.md` | The tailored CV — canonical, authored from `master-cv.json` |
| `<candidate>-<company>-cv.txt` / `.docx` / `.pdf` | Rendered from the `.md` by `scripts/render_cv.py`, one consistent template |
| `ATS_Report.txt` | `ats_weighted.py` output, integrity notes, human fit assessment |
| `<candidate>-<company>-cover-letter.md` | Formal cover letter |
| `Reply_Email_<Company>_<Recruiter>.md` | Ready-to-send reply plus a "Before you send" checklist. Only when there is a named recruiter or agency approach |
| `Role_Brief.md` | The main working document (structure below) |
| `pack.json` | `{ "notion_page_id", "nnn", "company", "role", "fit_score", "ats_score" }` — binds folder ⇄ card |

## Tailoring the CV

Start from `master-cv.json` named in the config. **Read it, never edit it** — the
tailored `.md` is a derived artefact. Never invent skills, tools or proof points,
and never fabricate contact details to clear a scorer blocker.

- **Brevity beats coverage.** Drop everything the JD does not ask for, including
  whole sub-engagements. Target ~700–850 body words. A CV that scores 100% and
  runs to three pages loses to a focused two-page one in a six-second screen.
- **Lead with the identity the JD wants** in the headline sub-title and the first
  summary line. The sub-title is a single clean role title ("Senior Software
  Engineer"), never a keyword string mirroring the JD.
- **Surface the strongest scale evidence up top** — for this profile, the tier-1
  banking and capital-markets work, the 10M+ daily transactions, the named
  institutional clients (LSEG, Access Bank).
- **Reframe by role type.** Java perm role → lead the Java backend identity,
  present consulting work backend-first. AI/product role → lead the AI systems
  work. Same facts, different ordering.
- **No em dashes** (U+2014) anywhere. En dashes in date ranges are fine.
- **New skills reconcile back.** If a JD forces a genuinely real skill the master
  lacks, add it to `master-cv.json` (`skills.core`/`familiar` and the relevant
  bullet) in the same pass. Otherwise the master rots.

Render with `python3 scripts/render_cv.py <stem>.md` — emits the `.txt`, `.docx`
and `.pdf`. The rendered files are ATS-safe by construction: single column, no
tables, no images, standard headings.

## The ATS gate

```bash
python3 scripts/ats_weighted.py --cv <stem>.txt --jd jd.txt \
        --title "<Company> <Role>" --report ATS_Report.txt
```

Terms are parsed from the JD and weighted: 3.0 under essential / responsibilities
headings, 1.5 in the body, 1.0 under desirable. Weighted coverage is the number
to report.

**Gate: weighted coverage ≥ 0.85 and zero formatting blockers. Iterate the CV,
not the scorer.** Two honest-failure cases:

- **A term is missing because the skill is not real.** Leave it missing; write an
  integrity note. A high score on a CV that cannot survive a technical screen is
  worse than a lower honest one — the cost lands in an interview, not a filter.
- **A blocker cannot be cleared truthfully** (e.g. no phone in the master by
  design). Record it, never invent one, and say plainly the gate failed on that
  known item.

Append to `ATS_Report.txt`: integrity notes (what was qualified, what was omitted
and why) and a human fit assessment (Strong / Adequate / Gap, x out of 10).

## Role brief structure

1. **Snapshot table** — title, client, supplier, recruiter, location, duration,
   type, rate or band, right to work, ATS result, Fit Score, human fit
2. **Verification line** — date checked, posting age, applicant count, any
   collision or blocking risk, with a numbered plan
3. **Requirement → evidence map** — one row per essential requirement, naming the
   specific engagement (from the master CV) that evidences it
4. **The gaps, and how to hold them** — the exact line to say out loud, plus the
   five or six specific facts to learn so the answer comes from study, not
   analogy. Naming a gap without a way to hold it just makes the user anxious
5. **Commercial notes** — rate anchor / landing / floor, IR35 or comp mechanics,
   supplier due diligence, what to confirm before signing. Flag, do not decide;
   note tax and IR35 mechanics are general information, not advice
6. **Likely screening questions**, and where to prepare each
7. **Questions to ask them**
8. **Pack contents table**

## Research before writing the brief

Web-search and record, with URLs. Do not state a benchmark you did not look up.

- The **end client** and the **supplier**. For agency/consultancy approaches,
  check the UK entity at Companies House (incorporation date, registered address,
  SIC code, filing status) against the website's claims. A young or dormant-coded
  entity behind a big-sounding website is a due-diligence question about who
  contracts and pays, not an accusation
- **Comp benchmark** for that title, city and IR35 status
- **Interview process**, if published
- Anything about the client's tech estate that shapes the conversation

## Same-end-client collision check

Before building, scan recent `Career/NNN_*` folders and the board for a role of
the same shape (title, city, duration, IR35 status, core stack) from a
**different** agency. Agencies push the same end-client requirement, and a
duplicate submission usually kills the candidate at both. Do this even when the
client is not named. If found, say so loudly in the brief and put a
right-to-represent question in the recruiter reply.

## Writing style

Plain, human, direct. Short sentences. No filler. No em dashes. The recruiter
reply has to read like the user wrote it, not a template — it is the first
writing sample the recruiter sees.
