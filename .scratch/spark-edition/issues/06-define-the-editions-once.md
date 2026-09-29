# Define the Editions once, in `tools/editions.py`

Type: task
Status: claimed
Blocked by: 01

## Question

Several guarantees are written out more than once, with literal copies that would drift once there
are two Editions. The allowlist `{pandas, numpy, sqlglot}` alone appears at
`tools/export_clean.py:51`, `tests/test_toolbox_checks.py:25` and `tests/test_levels.py:25`.
Make one dev-side registry and read everything from it.

`tools/editions.py` holds:

- `EDITIONS`, keyed by package (`sql_composer`, later `spark_composer`), each with its product
  text and library;
- `EXPORTED = ("sql_composer",)` until ticket 26;
- the import tiers: SHARED (`pandas`, `numpy`), and per Edition what `writing.py` and
  `engine.py` may add;
- the file classes: `EDITION_FILES` (`writing.py`, `engine.py`), `SHARED_FILES`,
  `VERBATIM_FILES` (`CHANGES.md`) and `PAGES` (`examples.html`);
- `DECLARED_DIFFERENCES = []` and `LAYOUT_MIRRORS_SQLGLOT = "30.19.0"`;
- `swap(text)`, the package and product swap. It fails closed on any leftover spelling
  (`sql[\W_]{0,2}composer` in any case), on a forbidden word in a canonical shared file, on a
  result that doesn't parse, and on an unclassified file.

Rewire `export_clean.py:51` and its message at `:254-255`, `test_toolbox_checks.py:25` and the
ruff paths at `:93-94`, and `test_levels.py:25` (Worked examples get SHARED only; none imports
sqlglot today). Add `tools` to the pytest `pythonpath`. `sql_composer` keeps a per-file exception
that lets every file import sqlglot, which ticket 13 empties. Unit tests go in
`tests/test_editions.py`.

## Done when

The Definition of done in `CLAUDE.md` holds, pytest is green at both sqlglot ends, and a grep finds
no other allowlist literal.
