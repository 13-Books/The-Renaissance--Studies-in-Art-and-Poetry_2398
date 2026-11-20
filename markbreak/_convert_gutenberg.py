#!/usr/bin/env python3
"""One-shot: Gutenberg 2398.txt -> MarkBreak spine under markbreak/."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "2398.txt"
OUT = Path(__file__).resolve().parent
COVER_SRC = ROOT / "cover.png"

ASTERISK_BREAK = re.compile(r"^\s*(\*\s+)+\*\s*$")

CHAPTERS = [
    ("TWO EARLY FRENCH STORIES", "Two Early French Stories", "chapter"),
    ("PICO DELLA MIRANDOLA", "Pico della Mirandola", "chapter"),
    ("SANDRO BOTTICELLI", "Sandro Botticelli", "chapter"),
    ("LUCA DELLA ROBBIA", "Luca della Robbia", "chapter"),
    ("THE POETRY OF MICHELANGELO", "The Poetry of Michelangelo", "chapter"),
    ("LEONARDO DA VINCI", "Leonardo da Vinci", "chapter"),
    ("THE SCHOOL OF GIORGIONE", "The School of Giorgione", "chapter"),
    ("JOACHIM DU BELLAY", "Joachim du Bellay", "chapter"),
    ("WINCKELMANN", "Winckelmann", "chapter"),
    ("CONCLUSION*", "Conclusion", "afterword"),
]


def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:60]


def yaml_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def strip_pg_shell(text: str) -> str:
    start = text.find("*** START OF THIS PROJECT GUTENBERG EBOOK")
    if start == -1:
        raise SystemExit("missing Gutenberg START marker")
    start = text.find("\n", start) + 1
    end = text.find("*** END OF THIS PROJECT GUTENBERG EBOOK")
    if end == -1:
        raise SystemExit("missing Gutenberg END marker")
    body = text[start:end]
    # Some PG plaintexts leave a prose "End of …" line before the END marker.
    body = re.sub(
        r"\nEnd of (the )?Project Gutenberg EBook[^\n]*\n?\s*$",
        "\n",
        body,
        flags=re.I,
    )
    return body


def body_to_markdown(raw: str) -> str:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    lines = [ln.rstrip() for ln in raw.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    paras: list[str] = []
    buf: list[str] = []
    verse: list[str] = []

    def flush_prose() -> None:
        nonlocal buf
        if not buf:
            return
        joined = " ".join(x.strip() for x in buf if x.strip())
        buf = []
        if not joined:
            return
        m = re.match(r"^\[Illustration:\s*(.*)\]\s*$", joined, re.S)
        if m:
            note = re.sub(r"_([^_]+)_", r"*\1*", m.group(1).strip())
            paras.append(f"> *Illustration:* {note}")
            return
        joined = re.sub(r"_([^_]+)_", r"*\1*", joined)
        # Footnote markers like [1] stay as-is
        paras.append(joined)

    def flush_verse() -> None:
        nonlocal verse
        if not verse:
            return
        q: list[str] = []
        for v in verse:
            t = v.strip()
            if not t:
                q.append(">")
            else:
                t = re.sub(r"_([^_]+)_", r"*\1*", t)
                q.append(f"> {t}")
        paras.append("\n".join(q))
        verse = []

    for ln in lines:
        if ASTERISK_BREAK.match(ln):
            flush_verse()
            flush_prose()
            paras.append("---")
            continue
        if ln.startswith("  ") and ln.strip():
            flush_prose()
            verse.append(ln)
            continue
        if verse:
            flush_verse()
        if not ln.strip():
            flush_prose()
            continue
        buf.append(ln)
    flush_verse()
    flush_prose()
    return "\n\n".join(paras).strip() + "\n"


def find_exact(lines: list[str], label: str, start: int = 0) -> int:
    for i in range(start, len(lines)):
        if lines[i].strip() == label:
            return i
    raise SystemExit(f"marker not found: {label!r}")


def main() -> None:
    text = strip_pg_shell(SRC.read_text(encoding="utf-8", errors="replace"))
    lines = text.split("\n")

    dedication_idx = find_exact(lines, "Dedication")
    preface_idx = find_exact(lines, "PREFACE")
    contents_idx = find_exact(lines, "CONTENTS")

    # First essay after the CONTENTS listing
    first_essay = find_exact(lines, CHAPTERS[0][0], contents_idx + 1)

    dedication_raw = "\n".join(lines[dedication_idx + 1 : preface_idx])
    preface_raw = "\n".join(lines[preface_idx + 1 : contents_idx])

    chapter_starts: list[tuple[int, str, str, str]] = []
    search_from = first_essay
    for marker, title, role in CHAPTERS:
        idx = find_exact(lines, marker, search_from)
        chapter_starts.append((idx, marker, title, role))
        search_from = idx + 1

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.md"):
        if old.name in {"CONVERSION.md", "README.md"}:
            continue
        old.unlink()

    (OUT / "meta.md").write_text(
        """\
---
title: "The Renaissance: Studies in Art and Poetry"
author: "Walter Pater"
language: en
publisher: "Project Gutenberg"
---

Sixth edition. Public domain in the USA (Project Gutenberg EBook #2398).
""",
        encoding="utf-8",
    )

    spine: list[tuple[str, str]] = []

    dedication_md = body_to_markdown(dedication_raw)
    (OUT / "00-dedication.md").write_text(
        f"""\
---
title: "Dedication"
role: dedication
---

# Dedication

{dedication_md}
""",
        encoding="utf-8",
    )
    spine.append(("00-dedication.md", "dedication"))

    preface_md = body_to_markdown(preface_raw)
    (OUT / "01-preface.md").write_text(
        f"""\
---
title: "Preface"
role: preface
---

# Preface

{preface_md}
""",
        encoding="utf-8",
    )
    spine.append(("01-preface.md", "preface"))

    for i, (idx, _marker, title, role) in enumerate(chapter_starts):
        end = (
            chapter_starts[i + 1][0]
            if i + 1 < len(chapter_starts)
            else len(lines)
        )
        raw = "\n".join(lines[idx + 1 : end])
        body = body_to_markdown(raw)
        seq = i + 2
        fname = f"{seq:02d}-{slugify(title)}.md"
        heading = "# Conclusion" if role == "afterword" else f"# {title}"
        (OUT / fname).write_text(
            f"""\
---
title: {yaml_quote(title)}
role: {role}
---

{heading}

{body}
""",
            encoding="utf-8",
        )
        spine.append((fname, role))

    (OUT / "99-colophon.md").write_text(
        """\
---
title: "Colophon"
role: colophon
---

# Colophon

This MarkBreak edition is converted from Project Gutenberg EBook #2398,
*The Renaissance: Studies in Art and Poetry* by Walter Pater.
Public domain in the USA.

Source repository: https://github.com/13-Books/The-Renaissance--Studies-in-Art-and-Poetry_2398  
Gutenberg: https://www.gutenberg.org/ebooks/2398
""",
        encoding="utf-8",
    )
    spine.append(("99-colophon.md", "colophon"))

    spine_yaml = "\n".join(f'  - {{ file: "{f}", role: {r} }}' for f, r in spine)
    (OUT / "book.md").write_text(
        f"""\
---
role: toc
meta: meta.md
spine:
{spine_yaml}
---

# The Renaissance: Studies in Art and Poetry

Walter Pater (sixth edition). MarkBreak spine.
""",
        encoding="utf-8",
    )

    if COVER_SRC.exists():
        shutil.copy2(COVER_SRC, OUT / "cover.png")

    print(f"Wrote MarkBreak tree under {OUT}")
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name}")

    from _build_online import main as build_online

    build_online()


if __name__ == "__main__":
    main()
