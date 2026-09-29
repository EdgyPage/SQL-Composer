# A conftest that knows the Edition, and tests with no hard-coded folder

Type: task
Status: claimed
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
