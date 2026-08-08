#!/usr/bin/env python3
"""
Build the flat `.skill` archives for claude.ai / Cowork upload.

Same source, two shapes (the principle from Cueversa's own package-skill.mts):
  - Claude Code loads the plugin from plugins/cueversa/ and prefixes every skill
    as `cueversa:<name>` at load time.
  - claude.ai / Cowork have no plugin namespace, so this script bakes the prefix
    into the archive: each skill is staged with its frontmatter `name:` rewritten
    to `cueversa-<name>` and zipped to dist/cueversa-<name>.skill, whose single
    top-level folder is `cueversa-<name>/` with SKILL.md at its root.

A `.skill` file is just that zip. Upload it under Settings -> Customize -> Skills.

Run:  python3 scripts/package.py
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "plugins" / "cueversa" / "skills"
DIST = ROOT / "dist"
PREFIX = "cueversa"

NAME_RE = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)
DESC_RE = re.compile(r"^description:\s*[>|]?-?\s*\S", re.MULTILINE)


def frontmatter(skill_md: str) -> str:
    parts = skill_md.split("---", 2)
    if len(parts) < 3:
        return ""
    return parts[1]


def validate(skill_dir: Path) -> tuple[bool, str]:
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return False, "no SKILL.md"
    fm = frontmatter(md.read_text(encoding="utf-8"))
    if not fm:
        return False, "no frontmatter block"
    m = NAME_RE.search(fm)
    if not m:
        return False, "frontmatter has no `name`"
    if m.group(1) != skill_dir.name:
        return False, f"name `{m.group(1)}` != folder `{skill_dir.name}`"
    # description present and substantial enough to trigger
    desc_line = next((l for l in fm.splitlines() if l.strip().startswith("description:")), "")
    # rough length gate: the whole frontmatter minus name/description keys
    body = fm.replace(desc_line, "")
    if not DESC_RE.search(fm) or len(fm) < 120:
        return False, "description missing or too short to trigger"
    return True, m.group(1)


def stage_and_zip(skill_dir: Path, name: str) -> Path:
    archive_name = f"{PREFIX}-{name}"
    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / archive_name
        shutil.copytree(
            skill_dir,
            staged,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )
        # Rewrite the frontmatter name so claude.ai shows `cueversa-<name>`.
        md = staged / "SKILL.md"
        text = md.read_text(encoding="utf-8")
        text = NAME_RE.sub(f"name: {archive_name}", text, count=1)
        md.write_text(text, encoding="utf-8")

        DIST.mkdir(exist_ok=True)
        out = DIST / f"{archive_name}.skill"
        out.unlink(missing_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(staged.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(Path(tmp)))
        return out


def main() -> int:
    if not SKILLS_DIR.exists():
        print(f"no skills dir at {SKILLS_DIR}", file=sys.stderr)
        return 1
    skills = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skills:
        print("no skills found", file=sys.stderr)
        return 1

    failed = []
    built = []
    for skill in skills:
        ok, info = validate(skill)
        if not ok:
            failed.append((skill.name, info))
            print(f"  SKIP {skill.name}: {info}")
            continue
        out = stage_and_zip(skill, info)
        kb = out.stat().st_size / 1024
        built.append(out)
        print(f"  built {out.relative_to(ROOT)} ({kb:.1f} KB)")

    print(f"\n{len(built)} archive(s) in {DIST.relative_to(ROOT)}/")
    if failed:
        print(f"{len(failed)} skill(s) skipped — fix frontmatter and re-run.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
