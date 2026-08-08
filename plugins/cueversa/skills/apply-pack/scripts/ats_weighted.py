#!/usr/bin/env python3
"""
Weighted ATS benchmark for a tailored CV against a job description.

Difference from the older job-apply/scripts/ats_score.py: that scorer matches a
FIXED lexicon. This one parses the JD itself, so it also catches role-specific
terms (Azure Service Bus, Document Database, technical governance, DDD, ...)
that a fixed lexicon misses, and it weights them:

  weight 3.0  term appears under an "essential" / "must have" / "responsibilities" heading
  weight 1.5  term appears anywhere else in the JD body
  weight 1.0  term appears under a "desirable" / "nice to have" / "bonus" heading

Weighted coverage = sum(weights of matched terms) / sum(weights of all terms).
That is the number to report. Raw coverage (unweighted) is reported alongside.

Formatting blockers follow the CV-workflow rule: single column, standard
headings, parseable contact, no em dash (U+2014).

Usage:
    python3 ats_weighted.py --cv cv.txt --jd jd.txt
    python3 ats_weighted.py --cv cv.txt --jd jd.txt --report ATS_Report.txt --title "Company Role"
    python3 ats_weighted.py --cv cv.txt --jd jd.txt --json
"""
from __future__ import annotations

import argparse
import json
import re

# Multi-word terms are checked before single words so "spring boot" is not
# double counted as "spring". Extend freely: an unmatched entry costs nothing.
TERM_BANK = [
    # languages / frameworks
    "java", "java 17", "java 21", "spring boot", "spring cloud", "spring framework",
    "spring data", "hibernate", "jpa", "kotlin", "python", "c#", ".net", "javascript",
    "typescript", "node.js", "react",
    # architecture
    "microservices", "microservice", "monolith", "distributed systems", "cloud-native",
    "event-driven", "event driven", "event sourcing", "cqrs", "domain-driven design",
    "domain driven design", "ddd", "hexagonal", "solution design", "architecture review",
    "architectural review", "technical governance", "architecture governance",
    "design patterns", "scalable", "highly available", "high availability", "secure",
    "asynchronous", "async", "high-volume", "high volume", "throughput", "low latency",
    "idempotency", "resilience", "api-first", "backend-for-frontend", "bff",
    # messaging
    "kafka", "rabbitmq", "azure service bus", "service bus", "azure event hub",
    "event hub", "event hubs", "messaging", "message broker", "pub/sub", "queue",
    "streaming", "stream processing",
    # data
    "document database", "document db", "nosql", "mongodb", "cosmos db", "cassandra",
    "dynamodb", "redis", "elasticsearch", "postgresql", "postgres", "oracle", "sql",
    "data model", "data models", "access patterns", "indexing", "aggregation",
    "sharding", "partitioning",
    # cloud / devops
    "azure", "aws", "gcp", "kubernetes", "aks", "docker", "terraform", "bicep",
    "infrastructure as code", "ci/cd", "devops", "azure devops", "jenkins",
    "github actions", "gitlab", "apim", "api management", "key vault", "entra id",
    "application insights", "observability", "opentelemetry", "monitoring",
    # apis
    "rest", "rest api", "restful", "api", "grpc", "graphql", "soap", "oauth2", "openapi",
    # ways of working / leadership
    "agile", "scrum", "code review", "mentor", "mentoring", "coaching",
    "technical leadership", "technical lead", "tech lead", "lead", "best practices",
    "stakeholder", "stakeholder management", "problem-solving", "problem solving",
    "analytical thinking", "delivery", "squad", "squads", "tdd", "bdd", "unit test",
    "junit", "mockito", "pair programming", "technical excellence", "roadmap",
]

ESSENTIAL_HEADINGS = re.compile(
    r"(essential|must[- ]have|required|requirements|responsibilit|your role|the role|key skills|core skills)",
    re.I,
)
DESIRABLE_HEADINGS = re.compile(
    r"(desirable|nice[- ]to[- ]have|bonus|advantageous|preferred|plus)", re.I
)
STANDARD_HEADINGS = [
    "experience", "education", "skills", "summary", "profile",
    "certifications", "projects", "employment", "expertise",
]


def _present(term: str, text: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None


def _count(term: str, text: str) -> int:
    return len(re.findall(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text))


def _section_weights(jd: str) -> dict[str, float]:
    """Walk the JD line by line, tracking which section each line sits under."""
    weights: dict[str, float] = {}
    section = "body"
    for line in jd.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # A short line with no trailing period reads as a heading.
        looks_like_heading = len(stripped) < 80 and not stripped.endswith(".")
        if looks_like_heading:
            if DESIRABLE_HEADINGS.search(stripped):
                section = "desirable"
            elif ESSENTIAL_HEADINGS.search(stripped):
                section = "essential"
        w = {"essential": 3.0, "desirable": 1.0, "body": 1.5}[section]
        low = stripped.lower()
        for term in TERM_BANK:
            if _present(term, low):
                weights[term] = max(weights.get(term, 0.0), w)
    return weights


def _dedupe_subsumed(terms: list[str]) -> list[str]:
    """Drop a single word when a multi-word term containing it is also required."""
    multi = [t for t in terms if " " in t]
    out = []
    for t in terms:
        if " " not in t and any(re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", m) for m in multi):
            continue
        out.append(t)
    return out


def score(cv_text: str, jd_text: str) -> dict:
    cv_l = cv_text.lower()
    weights = _section_weights(jd_text)
    required = _dedupe_subsumed(sorted(weights))
    weights = {t: weights[t] for t in required}

    matched = [t for t in required if _present(t, cv_l)]
    missing = [t for t in required if t not in matched]

    total_w = sum(weights.values()) or 1.0
    matched_w = sum(weights[t] for t in matched)
    weighted_cov = matched_w / total_w
    raw_cov = (len(matched) / len(required)) if required else 1.0

    words = re.findall(r"[a-zA-Z0-9#+./]+", cv_text)
    n_words = len(words)

    blockers = []
    if "\t" in cv_text or re.search(r"\|\s*\w+\s*\|", cv_text):
        blockers.append("possible table or multi-column layout (use single column plain text)")
    if not any(h in cv_l for h in STANDARD_HEADINGS):
        blockers.append("no standard section headings detected")
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", cv_text):
        blockers.append("no parseable email in contact block")
    if chr(0x2014) in cv_text:
        blockers.append("em dash present (U+2014), remove per style rule")

    # Body target is 700-850 words per the CV workflow rule. This count is the
    # whole extracted document (contact block, section headings, education), so
    # the band is set ~200 higher; a lead or principal CV legitimately runs to
    # two pages. Anything past 1050 is padding, trim it.
    length_ok = 650 <= n_words <= 1050
    fmt_score = 20 if not blockers else max(0, 20 - 5 * len(blockers))
    len_score = 10 if length_ok else (5 if 500 <= n_words <= 1200 else 0)
    ats = round(weighted_cov * 70 + fmt_score + len_score)

    hits = sorted(
        ((t, _count(t, cv_l), weights[t]) for t in matched),
        key=lambda x: (-x[2], -x[1], x[0]),
    )

    passed = weighted_cov >= 0.85 and not blockers
    return {
        "ats_score": ats,
        "weighted_coverage_pct": round(weighted_cov * 100, 1),
        "raw_coverage_pct": round(raw_cov * 100, 1),
        "matched_count": len(matched),
        "required_count": len(required),
        "word_count": n_words,
        "length_ok": length_ok,
        "top_hits": hits[:20],
        "matched": matched,
        "missing": [{"term": t, "weight": weights[t]} for t in missing],
        "missing_essential": [t for t in missing if weights[t] >= 3.0],
        "formatting_blockers": blockers,
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL, iterate before submitting",
    }


def render(r: dict, title: str) -> str:
    bar = "=" * 62
    out = [bar, f"ATS BENCHMARK  |  {title}", bar]
    out.append(f"Weighted keyword coverage : {r['weighted_coverage_pct']}%   (target >= 85%)")
    out.append(
        f"Raw keyword coverage      : {r['raw_coverage_pct']}%   "
        f"({r['matched_count']}/{r['required_count']} terms)"
    )
    out.append(f"Word count                : {r['word_count']}  ({'ok' if r['length_ok'] else 'out of band'})")
    out.append(f"Formatting blockers       : {len(r['formatting_blockers'])}")
    out.append(f"ATS Score (0-100)         : {r['ats_score']}")
    out.append("")
    out.append("Top matched terms:")
    for term, n, _w in r["top_hits"]:
        out.append(f"   + {term}: {n}x")
    if r["missing"]:
        out.append("")
        out.append("Missing terms (weight in brackets):")
        for m in r["missing"]:
            out.append(f"   - {m['term']} [{m['weight']}]")
    for b in r["formatting_blockers"]:
        out.append(f"   blocker: {b}")
    out.append(bar)
    out.append(f"VERDICT: {r['verdict']}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cv", required=True)
    ap.add_argument("--jd", required=True)
    ap.add_argument("--title", default="tailored CV")
    ap.add_argument("--report", help="write a human-readable report to this path")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    cv = open(a.cv, encoding="utf-8", errors="ignore").read()
    jd = open(a.jd, encoding="utf-8", errors="ignore").read()
    r = score(cv, jd)

    if a.json:
        print(json.dumps(r, indent=2))
    else:
        print(render(r, a.title))
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(render(r, a.title) + "\n")


if __name__ == "__main__":
    main()
