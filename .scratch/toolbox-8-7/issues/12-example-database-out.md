# The Example database leaves the library

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

The user's words: "I do not want runable python code for examples and demos inside the main
library." And: "The users should consult the documentation and example htmls besides code
directly. If the user has to consult code directly, that's a usability failure." (Q26, Q27,
Q29, Q31.)

## Done when

- **Moved to dev only, outside `sqlglot_composer/`:**
  - `example_database.py`;
  - the part of `engine.py` that runs the Example database's queries.

  `engine.py` keeps the sqlglot check `__init__.py` runs. `tools/toolbox_registry.py` follows.
- **`example_database` leaves `public.py`'s `__all__`** and the star import. No Toolbox file
  imports it, and a test holds that.
- **Docstring `>>>` examples stay as documentation:**
  - they lose their `from sqlglot_composer import example_database` lines and use the tables
    by name (`job_runs`, ...);
  - dev's doctest run supplies those names;
  - every example still runs in dev's tests.
- **Messages and Templates** that name `connect(example_database)` name the user's own
  connection.
- **Dev's own users of the Example database** import it from its new place: the how-tos, the
  journeys, the Example projects, the usability loop, the Copilot and Excel evaluations.
- **The Upgrade** (ticket 14) rewrites a Project's `example_database` imports, and marks any it
  can't rewrite with what to do.
- **CONTEXT.md's Example database and Example project entries** say what this ticket built,
  as the map's Words have them: dev only, read on main as pages.
- **Before and after:** the Toolbox folder's size, and its import time.

## Answer

Built 2026-11-13, on dev at 96ec3d0a.

- **The Example database's new place.** It is `example_database/` at the repo's top, beside
  the Toolbox's folder. `tools/toolbox_registry.py` names it as `EXAMPLE_DATABASE`.
  - `example_database/__init__.py` is the old `sqlglot_composer/example_database.py`, moved
    with git. It holds the nine Table references, the rows, `query` and `execute`.
  - It gains `doctest_names()`: each table by name, plus `query` and `execute`. That is what
    every run of the Toolbox's docstring examples supplies: `tests/test_docstrings.py`,
    `tests/test_built_run.py` and `tools/example_gallery.py`, so the gallery and the Hive
    corpus too.
  - `example_database/executor.py` is the half of `engine.py` that ran its queries:
    `run_query`, `INSTALL_NEWER` and the rewrites. It imports sqlglot at its top, and calls
    `sqlglot.executor.execute` through its module, so the tests can still stand in a wrong
    executor.
  - `sqlglot_composer/engine.py` keeps only `check_installed` and its behaviour checks.
- **What holds it.**
  - `tests/repo/test_toolbox_checks.py`: no Toolbox file imports the Example database, the
    folder has no `example_database` attribute, `engine` has no `run_query`, the 118 public
    names leave it out, and ruff now reads `example_database/` too.
  - `tests/test_docstrings.py`: no public docstring names `example_database`, and every example
    still runs.
  - `tests/test_example_database.py` runs the package's own docstring examples.
  - `tests/repo/test_export_clean.py`: main's cheat sheet names no `example_database`.
- **Before and after**, measured from a copy of `sqlglot_composer/` at 96ec3d0a and from this
  branch, with the regenerated pages.
  - Folder size: 3,766,080 bytes before, 3,642,220 after (-123,860, 3.3%).
  - Its Python: 1,961,374 bytes before, 1,872,680 after.
  - `engine.py`: 50,966 bytes before, 5,462 after.
  - `example_database.py`'s 23,550 bytes are gone.
  - The two pages are smaller by about 35 KB, since their import lines went.
  - Import time, median of 7 fresh Pythons with sqlglot and pandas already imported: 0.193 s
    before, 0.179 s after.
  - Import time from a fresh Python, sqlglot and pandas included: 0.66 s both before and after.
    sqlglot and pandas are almost all of it. (An earlier 2.4 s was a cold disk cache, and 0.66 s
    once warm.)
  - The pages stay in the folder until ticket 13.
- **Dev's users import it from its new place.** Each moved to the new import:
  - the tests and journeys;
  - the how-tos and Worked examples;
  - the Example projects, whose setup cells read `import example_database` then
    `connect(example_database)`, as `tools/example_project.py`'s `EXAMPLE_CONNECTION` writes
    them;
  - the gallery, how-to page, Hive corpus and Formula workbook tools;
  - `tools/workflow_warehouse.py`, which runs on `executor.run_query`;
  - the Copilot evaluation and the Excel evaluation;
  - the usability loop. It copies `example_database/` into each run's `_loop/` beside
    `workflow_warehouse.py`, and hashes it among the loop's files. Giving a Project the team's
    connection drops each line that imports the Example database, in either form.

  `tools/export_clean.py`'s dry run of the Example projects still passes: it runs
  `project.run_tables()` alone, which imports nothing of the Example database. Its tests pass
  too. On main, the Example projects' setup cells would not import until ticket 13 takes them
  off main.
- **For ticket 14: the import forms a Project may hold.** They can be in any notebook
  (`tables/`, `admin/`, `admin/workflows/`, `scheduled_runs/`), `warehouse.py`, `references/`,
  `building_blocks/`, or a Template the user edited in `admin/templates/`.
  1. `from sqlglot_composer import example_database` on a line of its own. The 8.6 step writes
     it, with `connect(example_database)` under it, into each setup cell where `conn` was the
     Example database (`upgrades.EXAMPLE_CONNECTION`). The Example projects held it from 8.6.
     A warehouse.py from before 8.6 held it above `conn = example_database`.
  2. `from sqlglot_composer import example_database, project, ...`, the name among others, on
     one line or in brackets over several. The how-tos wrote it this way, such as 09 and 31.
  3. `from sqlglot_composer import example_database as <alias>`.
  4. `from sqlglot_composer.example_database import jobs, job_runs, ...`, names taken from
     the module.
  5. `import sqlglot_composer.example_database` or `sqlglot_composer.example_database.<x>`,
     reached through the package.
  6. No import at all: `from sqlglot_composer import *`, then `example_database.<x>`. The star
     import brought the name until 8.7, as the README's old step "Run a Worked example" told
     users to do (`jobs, job_runs = example_database.jobs, example_database.job_runs`). This
     can't be rewritten as an import: each use of the bare name is to be marked.

  What a use was for: `connect(example_database)`, `example_database.query` /
  `.execute`, and `example_database.<table>`.

  Until ticket 14's step exists, `tests/conftest.py`'s `AWAITING_ITS_REWRITE` handles the
  tests. It maps form 1 to `import example_database` for the upgrade comparison, and
  `rewrite_what_awaits_its_step` does the same for an upgraded Project the journeys run.
  Ticket 14 empties both.
- **The older Upgrade steps are left as they were.** `upgrades.py`'s earlier steps still write
  form 1, in `EXAMPLE_CONNECTION` and the 7.x warehouse.py texts. They are history the chain
  replays, and 8.7's step rewrites what they leave.
- **Outside the ticket, kept small.**
  - The README's Terms entry and step 4 no longer say the Example database ships. Step 4 is now
    "Read a Worked example". The name count is 118. The README's tutorial (`import
    example_database`, line 18, the Example projects section) is ticket 13's.
  - The gallery's and how-to page's headers no longer say it ships inside the Toolbox.
  - `docs/offline-audit.md` points at the executor's new place.
  - `docs/agents/standards.md` takes dev's own fix of three pointers (`how_to.html`,
    `examples.html`, `test_standard.py`). `tests/repo/test_pointers.py` failed on them at
    96ec3d0a, and dev has already fixed them in the same words.
  - The snapshot, `tests/snapshot/known.txt`, is written again from a whole passing run. What
    changes is warehouse.py's two refusals and what the edited examples print. The recorder
    now wraps `example_database.query` from its new place.

**Decided:** the Example database is a package at the repo's top, `example_database/`, not a
file in `tools/`. `import example_database` and `example_database.query` then read as before,
which keeps every user's edit to its import line, and it is plainly not the Toolbox.

**Decided:** the docstring examples name `query` and `execute` alone, as a Project's notebook
does after `from warehouse import query, execute`. They don't name `example_database.query`.
`sqlglot_composer/__init__.py`'s docstring, which `help(sqlglot_composer)` shows, says once
whose tables, `query` and `execute` they are (the beginner reader's suggestion).

**Decided:** a docstring that bound a table to its own name (`run_alerts =
example_database.run_alerts`) loses that line. One that bound a short name keeps it, as `runs
= job_runs`. A template a docstring writes into a Project defines `jobs` there as a
two-column `Table`, since a Project has no Example database to import it from.

**Decided:** warehouse.py's docstring and refusals say "such as connect(conn), where conn is
your team's connection", as its setup cell's comment already names `conn`. Its docstring loses
the sentence on the Example projects.

**Decided:** `example_database` is Level 0 in `tests/repo/test_levels.py`, as `references/`
is, since the Worked examples import its Table references.

**Decided:** `tools/export_clean.py`'s cheat sheet loses its one special case, a file line
that repeats its only name's line. It was there for `example_database.py` alone.

## Code review

Run 2026-11-13 against 96ec3d0a (`review-standards` and `review-spec`, Sonnet). Beginner
reader: [report](../reports/beginner-reader-ticket-12.md).

Standards found no breach of `docs/agents/standards.md`. Its judgement calls are answered here:

- `_dotted` is written twice, in `engine.py` and `executor.py`. Kept: reaching `engine._dotted`
  would add a private seam to `tests/repo/test_dead_code.py` for a two-line helper.
- `executor.py` reads `engine._NEWEST_TESTED` and `engine._BELOW`. Kept: both are already
  listed seams, and their reasons now name the executor's fix, so the range is still written
  once.
- The `executed` alias is moved code, left as it was.
- `EXAMPLE_IMPORTS` lists both forms on purpose. A Project from before 8.7, such as a frozen
  one a scenario brings in, holds the old form, and the filter's two uses are each one line.
- The executor's fix text is dev's alone, so it stays.

Spec found nothing implemented wrong. Answered here:

- the sizes and the import forms (above);
- the older Upgrade steps' texts and `AWAITING_ITS_REWRITE`, both for ticket 14 (above);
- the cheat sheet's special case (decided above);
- the README edits, and the README's `import example_database` lines, for ticket 13 (above);
- the Example projects' READMEs, which are true on dev and go with ticket 13.

Beginner reader: its suggestions 2 and 3, how-to 01's wording, and the README's Terms and step 4
wording are fixed. Its suggestion 1, main's README tutorial and Example projects, is ticket
13's. The report lists each item.
