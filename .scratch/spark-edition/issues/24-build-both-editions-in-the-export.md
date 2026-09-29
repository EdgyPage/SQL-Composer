# Build both Editions in the export, still shipping one

Type: task
Status: open
Blocked by: 15, 22

## Question

Make `tools/export_clean.py` able to build both folders, while `EXPORTED` still names only
`sql_composer`, so `main` can go on being re-exported as 2.1 until ticket 26.

- `build(source, into, when, editions=EXPORTED)`, with one `when` for every folder and
  `stamp_text(product, ...)`, so both folders carry the same export time and their own product.
- Per-Edition `_FILES` and the tiered import allowlist from `tools/editions.py`.
- A fresh-Python import of each stamped folder, with the other library blocked (importing
  `spark_composer` needs pyspark but no JVM).
- Checks: lockstep versions; generated copies current; the two Editions' descriptions equal
  apart from VERSION's value; the allowlist and the `git archive` cover the EXPORTED folders.
- Refusals: EXPORTED names a folder the commit lacks; the README names an Edition that isn't
  shipped.
- In `__init__`: a stamp reader that knows each product, and a stop for a file pasted in from the
  other Edition ("tables.py is from the other Edition"), tested both ways.

Tests build both Editions into a temp folder; the real export and `--preview` still produce the
sqlglot-only 2.1 tree.

## Done when

The Definition of done in `CLAUDE.md` holds; `tests/repo/test_export_clean.py` covers every new
refusal; `python tools/export_clean.py --preview <folder>` gives the same sqlglot-only tree as
before.
