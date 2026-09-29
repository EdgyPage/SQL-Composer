# Define the Editions once, in `tools/editions.py`

Type: task
Status: resolved
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

## Answer

`tools/editions.py` defines the Editions once: each Edition's folder, product, library and the
files that may import it; which Editions the export ships; the four kinds of file; the import
tiers; `imports_outside`, the one import checker the export and the toolbox checks both use; and
`swap()`, which refuses any name it can't be sure of. The three copies of `{pandas, numpy,
sqlglot}` are gone. `tools` is on the pytest path. pytest passes: 1,105 tests and one strict
xfail that ticket 14 turns on.

## Comments

**Build decisions.** The sqlglot exception names the eight SQL Composer files that import sqlglot
today rather than letting every file do so: stricter than asked, so `refusals.py` can't start
importing it; tickets 10-13 shrink the list and 13 empties it. A verbatim file may name neither
Edition, since the same bytes ship in both folders; that means ticket 14 must also word
`CHANGES.md` without either folder's name (it names `sql_composer` today), as ticket 15 requires
it byte-equal in both.

**Code review (2026-09-29), `3f1bcb9`.**

- *Standards:*
  - Fixed: "package" (on the Toolbox's _Avoid_ list) is gone: an Edition has a `folder`, and the
    ruff test lists `edition_folders`; the comment on `LAYOUT_MIRRORS_SQLGLOT` names the ticket
    that adds its test; the docstring says "almost the same Hive" and names the Example gallery
    page; `trees.py` leaves `SHARED_FILES` until ticket 12 adds the file; `EXPORTED` holds
    Edition objects and each Edition carries its library files, so no folder name is repeated;
    `DECLARED_DIFFERENCES` is an empty tuple until ticket 18 shapes its rows; `may_import` and
    `swap` each decide once; the import walk lives once, in `editions.imports_outside`, used by
    the export and by the toolbox check; the test names say what they check; the Levels message
    says "something both Editions may import".
  - Answered, not changed: `swap` goes one way by design, as the ticket named it.
- *Spec:*
  - Fixed: Spark Composer's `writing.py` may import only the standard library, as the map's
    import tiers say; the leftover pattern takes any run of separators; a canonical shared file
    that names Spark Composer is refused as well as one naming sqlglot or pyspark; the test that
    no canonical shared file names what only one Edition has is in place as a strict xfail, for
    ticket 14 to turn on; a copy can't be swapped again.
  - Answered, not changed: `imports_outside` meets only Edition folders, and the export calls it
    only on one, so a `KeyError` for any other folder is a bug in the export, not a refusal.

