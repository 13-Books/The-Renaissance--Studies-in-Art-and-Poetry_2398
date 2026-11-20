# Gutenberg → MarkBreak (The Renaissance)

## Source

| File | Role |
|------|------|
| `../2398.txt` | UTF-8 plain text |
| `../metadata.yaml` | → `meta.md` |
| `../cover.png` | Copied to `cover.png` |

## Shape

| File | Role |
|------|------|
| `book.md` | `toc` + spine |
| `meta.md` | publication record |
| `00-dedication.md` | `dedication` — To C.L.S. |
| `01-preface.md` | `preface` |
| `02`–`10-*.md` | `chapter` — nine studies |
| `11-conclusion.md` | `afterword` — the restored Conclusion |
| `99-colophon.md` | `colophon` |

The Gutenberg `CONTENTS` listing is omitted; the MarkBreak spine is the TOC.

## Steps

```powershell
python markbreak/_convert_gutenberg.py
```

## Mapping

- Strip PG START/END and trailing “End of the Project Gutenberg EBook…” line.
- Soft-wrapped paragraphs joined; `_italics_` → `*italics*`.
- Indented verse / quotations → Markdown blockquotes.
- Asterisk ornaments → thematic `---`.
