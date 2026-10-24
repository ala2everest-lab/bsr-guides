#!/usr/bin/env python3
"""One-off: turn the exported docs in raw/ into content/*.md files with front matter."""
import re
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "raw"
CONTENT = ROOT / "content"
CONTENT.mkdir(exist_ok=True)

REVIEWED = ("2026-10-15", "15 October 2026")


def strip_common(body: str) -> str:
    lines = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("Written by Alicja Salter"):
            continue
        if s.startswith("*Alicja Salter is a building surveyor"):
            continue
        if re.match(r"^[A-Z][a-z]{2} \d{1,2}, 20\d\d · @Alicja$", s):
            continue
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text


def write(order, slug, h1, title, desc, body, reviewed=REVIEWED):
    head = (
        f"order: {order}\nslug: {slug}\nh1: {h1}\ntitle: {title}\ndescription: {desc}\n"
        f"reviewed: {reviewed[0]}\nreviewed_human: {reviewed[1]}\n"
    )
    (CONTENT / f"{order:02d}-{slug}.md").write_text(head + "---\n" + strip_common(body), encoding="utf-8")


# Guide 1
g1 = (RAW / "g1.md").read_text(encoding="utf-8")
g1_body = g1.split("\n", 1)[1]  # drop the "# Guide 1 – ..." heading
write(
    1,
    "do-i-need-bsr-approval-to-refurbish-a-flat",
    "Do I need BSR approval to refurbish a flat in a high-rise block?",
    "Do I Need BSR Approval to Refurbish a High-Rise Flat? (England)",
    "If your block is a higher-risk building, most flat refurbishment work needs Building Safety Regulator approval before it starts. What triggers it, what's exempt and how long it takes.",
    g1_body,
)

# Guides 2-9 from the combined doc
combined = (RAW / "g2_10.md").read_text(encoding="utf-8")
sections = re.split(r"^## ", combined, flags=re.M)[1:]
for sec in sections:
    heading, rest = sec.split("\n", 1)
    m = re.match(r"Guide (\d+): (.+)", heading)
    if not m:
        continue  # skips "Page 10: About" (template with blanks)
    n = int(m.group(1))
    meta = dict(re.findall(r"^\| (URL|Title tag|Meta description|H1) \| (.+?) \|$", rest, flags=re.M))
    body = re.sub(r"^\|.*\|\n", "", rest, count=6, flags=re.M)  # drop the page-detail table (header+sep+4 rows)
    body = re.sub(r"^### ", "## ", body, flags=re.M)  # promote subheads to h2 on their own page
    slug = meta["URL"].rsplit("/", 1)[-1]
    write(n, slug, meta["H1"], meta["Title tag"], meta["Meta description"], body)

# Windows article (published 23 Oct 2026)
win = (RAW / "win.md").read_text(encoding="utf-8")
win_title, win_body = win.split("\n", 1)
write(
    10,
    "replacing-windows-in-a-high-rise-flat",
    win_title.lstrip("# ").strip(),
    "Replacing Windows in a High-Rise Flat: FENSA, BSR and 2026 Reforms",
    "Why FENSA self-certification doesn't work for windows in flats over 18 metres, what that means for BSR approval, and what the 2026 reforms might change.",
    win_body,
    ("2026-10-23", "23 October 2026"),
)
print(sorted(p.name for p in CONTENT.glob("*.md")))
