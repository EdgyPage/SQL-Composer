# Split the suite into shared, sqlglot-edition and repo tests

Type: task
Status: resolved
Blocked by: 07

## Question

Most tests are about the Toolbox's behaviour and will run against both Editions. Some are about
sqlglot itself, and some are about the repo. Separate them:

- `tests/sqlglot_edition/` takes what only the sqlglot edition can pass:
  `test_escaping_cases.py`; `test_escaping_toolbox.py:81-85`, `:117-154` and `:209-245`;
  `test_example_database.py:56-59` and `:118-136`; `test_statements.py:160-162`;
  `test_worked_example_regrouping.py:42-45` and `:58-75`;
  `test_worked_example_latest_and_top_n.py:60-65`; `test_example_gallery.py:182-187` and
  `:271-273`; `test_import_self_check.py:181-251`.
- `tests/repo/` takes the repo-level tests (hooks, export, pointers, levels, toolbox checks),
  with their `ROOT` fixed. They run once, in the default run.
- Edition-only files get unique basenames (`test_sqlglot_*.py`, `test_spark_*.py`), with a repo
  test that every basename under `tests/` is unique (pytest's prepend import mode refuses
  duplicates).
- `pytest_ignore_collect` skips the other Edition's folder, and a `UsageError` stops a run that
  names it explicitly.
- A repo test checks that shared tests import neither sqlglot nor pyspark.

## Done when

The Definition of done in `CLAUDE.md` holds, the total test count is unchanged (moved, none lost),
`grep -l sqlglot tests/*.py` finds only prose, and pytest is green at both sqlglot ends.

## Answer

The suite has three parts (`ea4eb50`):

- **Shared tests** sit directly in `tests/`, run against every Edition, and import neither
  sqlglot nor pyspark.
- **`tests/sqlglot_edition/`** holds what only SQL Composer can pass, each file named
  `test_sqlglot_*`: sqlglot's escaping and read-back, the executor's limits, the sqlglot import
  stops and the golden.
- **`tests/repo/`** holds the repo's own checks, which run once, in SQL Composer's run.

The conftest collects only the chosen Edition's folder and stops a run given the other one. A
repo test holds every file name under `tests/` unique, the shared tests and the conftest free of
either library, and the collection rules themselves.

The review's counts: 1,079 tests before the split and 1,101 after (the 22 new layout checks),
with every per-file count adding up. Green at both sqlglot ends. `grep -l sqlglot tests/*.py` now
finds no import, only prose and the `--edition sqlglot` choice, since ticket 10 moved the
conftest's executor question into `engine.py`.

## Comments

**Code review (2026-09-29), `ea4eb50`.**

- *Spec:*
  - **Fixed:**
    - The layout test no longer exempts the conftest, which imports no library since ticket 10.
    - Unique names are held for every `.py` under `tests/`, helpers included, not only
      `test_*.py`.
    - Two layout tests hold the collection rules through the conftest's own hooks: which folders
      each run leaves out, and the UsageError for a folder the Edition leaves out.
    - The empty `# --- Where SQL text comes from ---` section is gone.
    - Tickets 11, 12, 14 and 19 name the tests' new paths. Ticket 12's new file is
      `test_sqlglot_trees_match.py`, after the `test_sqlglot_*` naming.
  - **Answered, not changed:**
    - Three listed tests stayed shared, since none needs sqlglot: the Date-partition bound
      refusal, the gallery's negative wording check, and
      `test_an_older_python_stops_the_import`. They pass in any Edition, so they run in both.
    - The commit message's "1,078 before the split" was off by one; the right count is above.
    - `pytest tests tests/spark_edition` skipping the folder silently is pytest's own handling of
      an ignored path given under another. The UsageError covers the run that names it alone.
- *Standards:*
  - **Fixed:**
    - `page_text` and the gallery's entry reader are one copy in the conftest
      (`gallery_entries`), and the import stop's expected text is one copy too (`import_stop`).
    - `WRITTEN` and `WRITTEN_IDS` moved to `tests/escaping_cases.py`.
    - The trailing and doubled blank lines are gone, and the new one-line docstrings close on
      their own line.
  - **Answered, not changed:**
    - `COMPARISONS` stays in both escaping tests. It names Toolbox functions, and
      `escaping_cases.py` holds plain data with no Toolbox import.
    - `EDITION_CHOICES` and `EDITION_FOLDERS` differ on purpose until Spark can be chosen: its
      folder must be left out before then. Ticket 16 adds `"spark"` and folds the two into one
      table, as its text now says.
