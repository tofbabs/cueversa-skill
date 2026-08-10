#!/usr/bin/env python3
"""Cueversa install walkthrough — poster PNG + stepped GIF, in the guide's palette.

Instructional graphic (not a screenshot of Anthropic's UI): a breadcrumb path
that animates through Settings -> Plugins -> Add -> Add marketplace -> From a
repository -> Sync, over a stable panel showing the repo URL, the Sync button,
and the four skills that get installed.
"""
import os

from PIL import Image, ImageDraw, ImageFont

# Output to docs/media/ relative to the repo (scripts/ -> repo root -> docs/media).
# macOS-only: uses the system SF Pro fonts. Run: python3 scripts/make_walkthrough.py
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "media")

S = 2                      # supersample for crisp type
W, H = 1120, 660           # logical canvas

# palette (guide light theme)
PAPER   = "#FBFDFC"; CARD = "#FFFFFF"; INK = "#16221E"; MUTED = "#5C6B64"
LINE    = "#E4EBE7"; LINE_SOFT = "#EFF4F1"
TEAL    = "#1D9E75"; TEAL_DEEP = "#0F6E56"; TEAL_SOFT = "#E4F5EE"; TEAL_INK = "#0B4A3A"
IDLE_BG = "#F1F5F3"; FIELD_BG = "#F7FAF8"

SFNS = "/System/Library/Fonts/SFNS.ttf"
MONO = "/System/Library/Fonts/SFNSMono.ttf"

def font(size, weight="Regular", mono=False):
    f = ImageFont.truetype(MONO if mono else SFNS, int(size * S))
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f

F_BRAND = font(13, "Bold")
F_TITLE = font(30, "Bold")
F_CHIP  = font(15, "Semibold")
F_CAP   = font(18, "Regular")
F_LABEL = font(12, "Semibold")
F_URL   = font(16, "Regular", mono=True)
F_BTN   = font(16, "Bold")
F_SKILL = font(15, "Medium", mono=True)
F_FOOT  = font(13, "Regular")

STEPS = ["Settings", "Plugins", "Add", "Add marketplace", "From a repository", "Sync"]
CAPTIONS = [
    "Open Claude, then go to Settings.",
    "In Settings, open Plugins.",
    "Click Add.",
    "Choose Add marketplace.",
    "Pick Add from a repository, then paste the URL below.",
    "Select the repository and click Sync.",
]
SKILLS = ["cueversa:setup", "cueversa:fetch-jobs", "cueversa:apply-pack", "cueversa:provide-update"]
REPO = "https://github.com/tofbabs/cueversa-skill/"


def sx(v):  # scale one coordinate
    return int(round(v * S))


class C:
    def __init__(self):
        self.img = Image.new("RGB", (W * S, H * S), PAPER)
        self.d = ImageDraw.Draw(self.img)

    def text(self, xy, s, f, fill, anchor="la"):
        self.d.text((sx(xy[0]), sx(xy[1])), s, font=f, fill=fill, anchor=anchor)

    def tw(self, s, f):
        return self.d.textlength(s, font=f) / S

    def rr(self, box, r, fill=None, outline=None, width=1):
        self.d.rounded_rectangle(
            [sx(box[0]), sx(box[1]), sx(box[2]), sx(box[3])],
            radius=sx(r), fill=fill, outline=outline, width=max(1, sx(width)),
        )

    def check(self, cx, cy, size, color):
        s = size
        pts = [(cx - s * 0.42, cy + s * 0.02), (cx - s * 0.12, cy + s * 0.32), (cx + s * 0.46, cy - s * 0.34)]
        self.d.line([(sx(p[0]), sx(p[1])) for p in pts], fill=color, width=sx(2.4), joint="curve")

    def chevron(self, cx, cy, color):
        pts = [(cx - 3, cy - 6), (cx + 3, cy), (cx - 3, cy + 6)]
        self.d.line([(sx(p[0]), sx(p[1])) for p in pts], fill=color, width=sx(2), joint="curve")


def render(active, synced):
    c = C()
    # header
    c.d.ellipse([sx(60), sx(50), sx(60 + 9), sx(50 + 9)], fill=TEAL)
    c.text((78, 47), "C U E V E R S A   ·   B E T A", F_BRAND, TEAL_DEEP)
    c.text((60, 74), "Install in Claude — one sync, all four skills", F_TITLE, INK)

    # breadcrumb rail
    x = 60
    y = 150
    ch = 42
    padx = 15
    for i, label in enumerate(STEPS):
        w = c.tw(label, F_CHIP) + padx * 2
        done = i < active
        cur = i == active
        if cur:
            c.rr((x, y, x + w, y + ch), ch / 2, fill=TEAL)
            tcol = "#F3FBF8"
        elif done:
            c.rr((x, y, x + w, y + ch), ch / 2, fill=TEAL_SOFT, outline=None)
            tcol = TEAL_INK
        else:
            c.rr((x, y, x + w, y + ch), ch / 2, fill=IDLE_BG)
            tcol = MUTED
        tx = x + padx
        if done:
            c.check(x + padx + 3, y + ch / 2, 12, TEAL)
            tx = x + padx + 18
            w += 15
            # widen chip for the check
            c.rr((x, y, x + w, y + ch), ch / 2, fill=TEAL_SOFT)
            c.check(x + padx + 3, y + ch / 2, 12, TEAL)
        c.text((tx, y + ch / 2 - 1), label, F_CHIP, tcol, anchor="lm")
        nx = x + w
        if i < len(STEPS) - 1:
            c.chevron(nx + 13, y + ch / 2, "#C4D2CB")
        x = nx + 26

    # caption
    cap = "Done — all four skills are installed." if synced else CAPTIONS[active]
    c.text((60, 226), cap, F_CAP, INK if synced else MUTED)

    # panel
    px0, py0, px1, py1 = 60, 268, 1060, 600
    c.rr((px0, py0, px1, py1), 16, fill=CARD, outline=LINE, width=1.4)

    # "Add from a repository" sub-label
    c.text((px0 + 30, py0 + 26), "ADD FROM A REPOSITORY", F_LABEL, TEAL_DEEP)

    # URL field
    fy = py0 + 54
    fh = 52
    fx0, fx1 = px0 + 30, px1 - 210
    c.rr((fx0, fy, fx1, fy + fh), 11, fill=FIELD_BG, outline=(TEAL if active >= 4 else LINE), width=1.6 if active >= 4 else 1.2)
    c.text((fx0 + 18, fy + fh / 2), REPO, F_URL, INK, anchor="lm")

    # Sync button
    bx0 = fx1 + 20
    bx1 = px1 - 30
    if synced:
        c.rr((bx0, fy, bx1, fy + fh), 11, fill=TEAL_SOFT, outline=TEAL, width=1.6)
        cxx = bx0 + 44
        c.check(cxx, fy + fh / 2, 16, TEAL_DEEP)
        c.text(((cxx + bx1) / 2 + 6, fy + fh / 2), "Synced", F_BTN, TEAL_DEEP, anchor="mm")
    else:
        hot = active == 5
        c.rr((bx0, fy, bx1, fy + fh), 11, fill=(TEAL_DEEP if hot else TEAL))
        c.text(((bx0 + bx1) / 2, fy + fh / 2), "Sync", F_BTN, "#F3FBF8", anchor="mm")

    # skills list
    ly = fy + fh + 34
    c.text((px0 + 30, ly), "INSTALLS", F_LABEL, MUTED)
    ly += 26
    rowh = 40
    gap = 14
    colw = (px1 - px0 - 60 - gap) / 2
    for i, name in enumerate(SKILLS):
        r, col = divmod(i, 2)
        rx0 = px0 + 30 + col * (colw + gap)
        rx1 = rx0 + colw
        ry0 = ly + r * (rowh + 12)
        if synced:
            c.rr((rx0, ry0, rx1, ry0 + rowh), 9, fill=TEAL_SOFT, outline=None)
            c.check(rx0 + 22, ry0 + rowh / 2, 15, TEAL_DEEP)
            c.text((rx0 + 42, ry0 + rowh / 2), name, F_SKILL, TEAL_INK, anchor="lm")
        else:
            c.rr((rx0, ry0, rx1, ry0 + rowh), 9, fill=FIELD_BG, outline=LINE_SOFT, width=1)
            c.d.ellipse([sx(rx0 + 15), sx(ry0 + rowh / 2 - 5), sx(rx0 + 25), sx(ry0 + rowh / 2 + 5)],
                        outline="#C4D2CB", width=sx(1.6))
            c.text((rx0 + 42, ry0 + rowh / 2), name, F_SKILL, MUTED, anchor="lm")

    # footer note
    foot = ("Type  /cueversa:setup  in a new chat to begin." if synced
            else "github.com/tofbabs/cueversa-skill")
    c.text((60, 622), foot, F_FOOT, MUTED)

    return c.img.resize((W, H), Image.LANCZOS)


# ---- build ----
frames = []
durations = []
for i in range(len(STEPS)):
    frames.append(render(active=i, synced=False))
    durations.append(1050 if i >= 4 else 780)
poster = render(active=5, synced=True)
frames.append(poster)
durations.append(2800)

os.makedirs(OUT, exist_ok=True)

# poster PNG at 2x for crispness
render(active=5, synced=True).resize((W * 2, H * 2), Image.LANCZOS).save(f"{OUT}/cueversa-install.png")

# gif
pal_frames = [f.convert("P", palette=Image.ADAPTIVE, colors=256, dither=Image.NONE) for f in frames]
pal_frames[0].save(
    f"{OUT}/cueversa-install.gif", save_all=True, append_images=pal_frames[1:],
    duration=durations, loop=0, disposal=2, optimize=True,
)
print("wrote cueversa-install.png and cueversa-install.gif")
