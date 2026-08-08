# Render spike — resolving open item #1 (the `render_cv.py` toolchain)

**Question:** can `cv.md` be rendered to `.docx` and `.pdf` on the Cowork /
code-execution sandbox using only pip-installable, pure-Python packages (no
pandoc, no libreoffice, no weasyprint system binaries)?

**Answer: yes.**

## Toolchain

| Output | Library | Availability |
|---|---|---|
| `.txt` | none — plain flatten | always |
| `.docx` | `python-docx` | preinstalled in the sandbox |
| `.pdf` | `fpdf2` (`pip install fpdf2`, pure Python) | one pip install, no system libs |

## Findings (each cost a failed run — the point of a spike)

1. **fpdf2 core fonts (Helvetica) are Latin-1 only.** An em-dash `—`, en-dash
   `–`, or a non-Latin name (`Łukasz`) throws "character outside the range of
   the font." Not width — encoding.

2. **Fix: a Unicode TTF, discovered not bundled.** `_find_unicode_font()` prefers
   a font bundled in `apply-pack/assets/`, then **matplotlib's DejaVuSans** (which
   is preinstalled in the sandbox — the real path there), then Linux DejaVu paths.
   If none is found it falls back to core Helvetica with the common typographic
   characters normalised to ASCII (`—`→`-`, smart quotes→straight) — which is
   also friendlier to ATS PDF parsers. `.txt` and `.docx` keep full Unicode
   regardless; only the core-font PDF fallback sanitizes.

3. **Arial Unicode (macOS) is excluded deliberately** — it triggers an fpdf2
   width bug when a bold heading precedes body text. DejaVu does not.

4. **The real width bug was ours:** fpdf2's `multi_cell` leaves the cursor at the
   right margin, so the next full-width cell saw ~0 space. Fixed with
   `new_x="LMARGIN", new_y="NEXT"` on every cell. This, not the font, was the
   recurring "not enough horizontal space" error.

## Verified

- **Sanitize branch** (no DejaVu): valid PDF, ASCII-normalised.
- **DejaVu branch** (matplotlib present = the sandbox): valid PDF with `Łukasz`
  and em-dash rendered as real Unicode.
- `.docx` validates (22 paragraphs); `.txt` keeps Unicode.

## Productionization note

For byte-for-byte determinism everywhere, bundle `DejaVuSans.ttf` +
`DejaVuSans-Bold.ttf` in `apply-pack/assets/` (permissive licence). The sandbox
already resolves DejaVu via matplotlib, so bundling is an optional hardening
step, not a blocker. Sample output: `tofunmi-adeyemi-monzo-cv.{txt,docx,pdf}`.
