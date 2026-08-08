#!/usr/bin/env python3
"""
Generic propensity scorer for the cueversa:fetch-jobs skill.

Answers one question deterministically: how likely is THIS user to actually
get THIS job? Outputs a Fit Score on a 0-10 scale that the Notion board sorts
on, so scoring a job and ranking the board are the same action.

Unlike a hardcoded personal scorer, every user-specific signal comes from the
profile section of fetch-jobs.config.json:

  skills                      - lower-cased tokens the user's CV can defend
  known_gaps                  - required-skill keywords the user cannot defend
  comp_floor / currency       - minimum acceptable comp (numeric)
  level_sweet_spot            - "mid" | "senior" | "staff" | "lead" | "principal"
  identity_keywords           - e.g. ["java", "backend"]; roles whose title and
                                must-haves match get a small identity bonus
  contract_friendly           - bool; contract roles get a boost if true
  flight_risk_perm_employers  - flagship employers where perm-without-referral
                                is penalised for this user

Weights (fixed): skills/JD match 50% (0-5), seniority+comp fit 25% (0-2.5),
signal strength 25% (0-2.5). Effort-to-apply is deliberately not weighted.

Usage:
    python3 score.py --config fetch-jobs.config.json < jobs.json > scored.json

Input: a JSON job dict or list of dicts. Keys (all optional, more = better):
    title, company, type ("Perm"|"Contract"|"FTE"|"Contractor"), level,
    comp_max (numeric max of the band in config currency), jd_must_haves [str],
    referral_available (bool), recruiter_warm (bool), days_since_posted (int),
    apply_channel (str), employer_key (str or null for masked agency listings)

Output: the same list with a "_score" dict added to each job:
    {"fit_score", "breakdown", "flags", "confidence_band"}
Run best_per_company() (via --active-employers) to add "_company_decision".
"""
from __future__ import annotations

import argparse
import json
import sys

LEVELS_BELOW = {"junior", "graduate", "associate", "mid", "intermediate"}
LEVELS_STRETCH = {"staff", "lead", "tech lead"}
LEVELS_OVERSHOOT = {"principal", "architect", "distinguished", "head", "director"}
DIRECT_CHANNELS = {"greenhouse", "ashby", "lever", "workday", "company-ats", "direct"}
AGGREGATOR_CHANNELS = {"linkedin-easy-apply", "indeed", "aggregator"}


def _tokens(values):
    return {str(v).strip().lower() for v in values or [] if str(v).strip()}


def _matches(skill: str, pool: set) -> bool:
    return any(skill == p or skill in p or p in skill for p in pool)


def _skills_match(job: dict, profile: dict):
    """0-5 points. Coverage of the JD's must-haves by the user's skill set."""
    must = [s.strip().lower() for s in job.get("jd_must_haves", []) if s.strip()]
    skills = _tokens(profile.get("skills"))
    gaps = _tokens(profile.get("known_gaps"))
    flags = []
    if not must:
        flags.append("no jd_must_haves parsed - skills score is a placeholder")
        return 3.5, flags

    covered = 0
    gaps_hit = []
    for skill in must:
        if _matches(skill, skills):
            covered += 1
        elif _matches(skill, gaps):
            gaps_hit.append(skill)

    coverage = covered / len(must)
    base = coverage * 5.0

    # Identity bonus: when the role title AND the must-haves speak the user's
    # primary identity (e.g. "java backend"), a clean current-identity match
    # materially improves screen pass-through.
    idents = _tokens(profile.get("identity_keywords"))
    title = job.get("title", "").lower()
    if idents and any(i in title for i in idents) and any(
        _matches(i, set(must)) or any(i in m for m in must) for i in idents
    ):
        base = min(5.0, base + 0.3)

    if gaps_hit:
        base = max(0.0, base - min(2.0, 0.6 * len(gaps_hit)))
        flags.append(
            f"hard must-have gap(s): {', '.join(gaps_hit)} (reframe or deprioritise)"
        )
    if coverage < 0.6:
        flags.append(f"skills coverage {coverage:.0%} < 60% target - weak ATS match")
    return round(base, 2), flags


def _seniority_comp(job: dict, profile: dict):
    """0-2.5 points. Level alignment against the sweet spot + comp floor."""
    flags = []
    pts = 2.5
    sweet = (profile.get("level_sweet_spot") or "senior").lower()
    level = (job.get("level") or "").lower()

    if not level or level.startswith(sweet) or level in {"sse", "senior i", "senior ii"} and sweet == "senior":
        pass
    elif level in LEVELS_STRETCH:
        if sweet in ("staff", "lead", "principal"):
            pass
        else:
            pts -= 0.5
            flags.append(f"level '{level}' is a mild stretch above the '{sweet}' sweet spot")
    elif level in LEVELS_OVERSHOOT:
        if sweet == "principal":
            pass
        else:
            pts -= 1.0
            flags.append(f"level '{level}' over-shoots the '{sweet}' identity - match CV language carefully")
    elif level in LEVELS_BELOW:
        if sweet in LEVELS_BELOW:
            pass
        else:
            pts -= 1.5
            flags.append(f"level '{level}' under-shoots - risk of over-qualified screen-out")

    floor = profile.get("comp_floor")
    cur = profile.get("currency", "")
    comp = job.get("comp_max", job.get("comp_gbp_max"))
    if comp is not None and floor:
        if comp < floor:
            pts -= 0.75
            flags.append(f"comp ~{cur}{comp:,} below {cur}{floor:,} floor")
    else:
        flags.append("comp unknown - not penalised, verify before applying")

    return round(max(0.0, pts), 2), flags


def _signal(job: dict, profile: dict):
    """0-2.5 points. Referral, warmth, freshness, channel, contract fit."""
    flags = []
    pts = 1.0

    if job.get("referral_available"):
        pts += 0.8
        flags.append("referral available - highest-leverage, bypasses comparative screen")
    if job.get("recruiter_warm"):
        pts += 0.4

    age = job.get("days_since_posted")
    if age is not None:
        if age <= 3:
            pts += 0.5
        elif age <= 7:
            pts += 0.3
        elif age > 21:
            pts -= 0.3
            flags.append(f"posting is {age}d old - likely deep applicant pool")

    channel = (job.get("apply_channel") or "").lower()
    if channel in DIRECT_CHANNELS:
        pts += 0.3
    elif channel in AGGREGATOR_CHANNELS:
        pts -= 0.1

    employer = (job.get("company") or "").lower()
    jtype = job.get("type", "Perm")
    flagships = _tokens(profile.get("flight_risk_perm_employers"))
    if (
        jtype == "Perm"
        and any(e in employer for e in flagships)
        and not job.get("referral_available")
    ):
        pts -= 0.6
        flags.append("perm flagship + no referral - comparative screen risk, get a referral first")

    if jtype in ("Contract", "Contractor") and profile.get("contract_friendly"):
        pts += 0.4
        flags.append("contract role - independent history is a strength here, prioritise")

    return round(max(0.0, min(2.5, pts)), 2), flags


def score_job(job: dict, profile: dict) -> dict:
    s_skills, f1 = _skills_match(job, profile)
    s_senior, f2 = _seniority_comp(job, profile)
    s_signal, f3 = _signal(job, profile)
    fit = max(0.0, min(10.0, round(s_skills + s_senior + s_signal, 1)))

    if fit >= 8.0 and not any("gap" in f for f in (f1 + f3)):
        band = "high"
    elif fit >= 6.5:
        band = "medium"
    else:
        band = "low"
    if band == "high" and any("stretch" in f or "over-shoot" in f for f in f2):
        band = "medium"

    return {
        "fit_score": fit,
        "breakdown": {
            "skills_match_0_5": s_skills,
            "seniority_comp_0_2p5": s_senior,
            "signal_0_2p5": s_signal,
        },
        "flags": f1 + f2 + f3,
        "confidence_band": band,
    }


def best_per_company(scored: list, existing_active_employer_keys=None) -> list:
    """
    Enforce one best-fit application per hiring employer.

    Each item needs "_score" and an "employer_key": the normalised DIRECT
    employer name, or None for agency listings whose real employer is hidden
    (those are never collapsed together). Items whose employer already has an
    active card, or lost to a higher-scoring role this run, are annotated
    "_company_decision": "backlog"; winners get "identified".
    """
    existing = set(existing_active_employer_keys or set())
    ranked = sorted(scored, key=lambda j: j.get("_score", {}).get("fit_score", 0), reverse=True)
    chosen = set()
    for item in ranked:
        key = item.get("employer_key")
        fit = item.get("_score", {}).get("fit_score", 0)
        if not key:
            item["_company_decision"] = "identified"
            item["_company_reason"] = "employer unknown (agency listing) - not collapsed"
        elif key in existing:
            item["_company_decision"] = "backlog"
            item["_company_reason"] = f"company already active on board ({key}) - park"
        elif key in chosen:
            item["_company_decision"] = "backlog"
            item["_company_reason"] = f"lower-fit duplicate at {key} this run"
        else:
            chosen.add(key)
            item["_company_decision"] = "identified"
            item["_company_reason"] = f"best fit at {key} (Fit {fit})"
    return ranked


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True, help="path to fetch-jobs.config.json")
    ap.add_argument(
        "--active-employers",
        default="",
        help="comma-separated employer_keys that already have an active card",
    )
    args = ap.parse_args()

    with open(args.config) as fh:
        cfg = json.load(fh)
    profile = cfg.get("profile", cfg)

    data = json.load(sys.stdin)
    jobs = data if isinstance(data, list) else [data]
    for job in jobs:
        job["_score"] = score_job(job, profile)

    active = {k.strip().lower() for k in args.active_employers.split(",") if k.strip()}
    out = best_per_company(jobs, active)
    json.dump(out, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
