# A conftest that knows the Edition, and tests with no hard-coded folder

Type: task
Status: resolved
Blocked by: 06

## Question

The Spark run (ticket 16) must choose its Edition before any Toolbox module is imported, but
`tests/conftest.py:16-30` imports sqlglot and the Toolbox at load. Prepare the ground, with the
sqlglot edition the only one for now:

- `tests/conftest.py` imports neither sqlglot nor the Toolbox at module level.
- Add the options `--edition` (only `sqlglot` accepted for now) and `--example-database`
  (`optional`, the default, or `required`, which turns a skip into a failure).
- The marker `needs_example_database`, registered in `pyproject.toml`, replaces `needs_executor`
  in the 11 modules that use it, and `example_database_cannot_run()` replaces `EXECUTOR_READY`.
- Add `toolbox_folder()`, `edition()`, `in_edition(text)` (the identity for now) and a report
  header naming the Edition.
- Replace the hard-coded folders: `tests/test_escaping_toolbox.py:60`,
  `tests/test_import_self_check.py:19-28`, `tests/test_toolbox_checks.py:24`,
  `tests/test_example_gallery.py:26` and `:62`.
- `tests/test_import_self_check.py` and `tests/test_export_clean.py` derive "2.1" from
  `TOOLBOX_VERSION`, so 3.0 won't need a test sweep.

## Done when

The Definition of done in `CLAUDE.md` holds, and `python -m pytest` passes with exactly the same
passed and skipped counts as before, at both sqlglot ends.

## Answer

`tests/conftest.py` chooses the Edition before any Toolbox module is imported: it loads neither
sqlglot nor the Toolbox, takes `--edition` (only `sqlglot`, SQL Composer, for now) and
`--example-database` (`optional`, or `required`, which fails where it would skip), and names the
Edition in the report header and again at the end of every run. The `needs_example_database`
marker replaced `needs_executor` in twelve modules, `skip_unless_the_example_database_runs()`
replaced `EXECUTOR_READY`, and the import self-check, escaping, toolbox and gallery tests read the
Edition's folder, product and version instead of writing `sql_composer` and "2.1". Passed and
skipped counts were unchanged at both ends of the sqlglot range (1,104 passed and one xfail at
30.19.0; 1,046 passed, 58 skipped and one xfail at 25.24.2).

## Comments

**Code review (2026-09-29), `75d809c`.**

- *Standards:*
  - Fixed: no "package", "library" or "engine" in the conftest's docstrings; the `--edition`
    help says `sqlglot` means SQL Composer; the gallery test reads every module through
    `toolbox_module()`; the export test's version text is `VERSION_TEXT`, so it doesn't share a
    name with `editions.EXPORTED`; the autouse fixture is `skip_without_the_example_database`,
    not the marker's name; `toolbox_module` has its return type; the conftest states each
    default once (in the options) and says what `_chosen` holds.
  - Answered, not changed: `--edition sqlglot` is the ticket's word for SQL Composer and is
    kept, since a library name is what a CI matrix reads; `f"{PRODUCT} {VERSION}"` stays
    written out in each expected message, where it reads as the message does.
- *Spec:*
  - Fixed: the run names its Edition at the end, since `-q` hides the header; the import check
    runs over every Edition folder that exists, not only the one under test; the gallery's
    stale-page message names the Edition's folder; the conftest docstring no longer says CI
    passes `--example-database required` (ticket 20 adds it).
  - Answered, not changed: `in_edition()` is gone. It was dead: the tests read the Edition's
    folder, product and version from `conftest.edition()`, which follows ticket 16's alias with
    no swap, and ticket 16's text says so now. `example_database_cannot_run()` still asks
    sqlglot; ticket 10 moves the question into each Edition's `engine.py`, before ticket 16
    blocks sqlglot. Twelve modules had `needs_executor`, not eleven.

