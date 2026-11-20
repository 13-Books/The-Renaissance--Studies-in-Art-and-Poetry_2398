#!/usr/bin/env python3
"""Concatenate book.md + spine bodies into book.online.md for markbreak.app ?url=."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def strip_yaml(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4 :].lstrip("\r\n")


def spine_files(book: str) -> list[str]:
    if not book.startswith("---"):
        return []
    end = book.find("\n---", 3)
    if end == -1:
        return []
    yaml = book[4:end]
    files: list[str] = []
    in_spine = False
    for line in yaml.splitlines():
        if re.match(r"^spine\s*:", line):
            in_spine = True
            continue
        if in_spine:
            if re.match(r"^\S", line) and line.strip():
                break
            m = re.search(r'file:\s*"([^"]+)"', line)
            if m:
                files.append(m.group(1))
    return files


def main() -> None:
    book = (ROOT / "book.md").read_text(encoding="utf-8")
    files = spine_files(book)
    parts = [book.rstrip()]
    for rel in files:
        child = (ROOT / rel).read_text(encoding="utf-8")
        parts.append("")
        parts.append(strip_yaml(child).rstrip())
    out = "\n\n".join(parts).rstrip() + "\n"
    (ROOT / "book.online.md").write_text(out, encoding="utf-8")
    print(f"wrote book.online.md ({len(out)} chars, {len(files)} spine files)")


if __name__ == "__main__":
    main()
