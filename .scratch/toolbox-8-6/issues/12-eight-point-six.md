# 8.6: the Upgrade step and the raise

Type: task
Status: resolved
Blocked by: 10
Size: M

## Question

The user named 8.6 (map, "The version").

## Done when

- `to_8_6` in `upgrades.py`'s STEPS: warehouse.py gains `connect`, `query` and `execute` as
  8.6 writes them, the user's `conn = ...` line and what it imports kept and marked to move
  into a `connect(...)` call; each Toolbox notebook's setup cell gains its `connect(...)` line;
  `scheduled_runs/`, the Template and `admin/scheduled_runs.ipynb` made.
- `tests/upgrade_from/8.5/` frozen from the Example projects as 8.5 left them, without their
  Lineage pages; the chain test runs 8.3 to 8.6.
- `version.txt` says 8.6.

## Answer

Built 2026-11-09.

- `upgrades.to_8_6`, `"8.6"` in STEPS, in order:
  1. **warehouse.py** (`_warehouse_as_8_6`), read with `ast`: its statements other than its
     docstring, `import pandas as pd` and a `query` and `execute` as 8.0 to 8.5 wrote them
     (compared without their docstrings) are "yours". **Decided: three cases.** Yours exactly
     `from sqlglot_composer import example_database` and `conn = example_database`, as
     start() set it: written as `project.WAREHOUSE_TEXT`, and every notebook below connected
     with `EXAMPLE_CONNECTION`, as `conn` was, so the Project runs as it did; nothing marked,
     a "Done for you" line saying so. Yours holding a statement that sets `conn` (an
     assignment or an import, as 8.2's comment showed): written as WAREHOUSE_TEXT with each
     of yours kept verbatim, by its line range, after `import pandas as pd` under
     `KEPT_CONNECTION_HEADING`, and one mark above the line setting conn; each notebook's
     line left `# connect(your_connection)`. **Decided: the kept lines stay live**, so
     `from warehouse import conn` and `connect(conn)` connect a notebook meanwhile, which the
     mark says. Otherwise (your own `query` or `execute`, no conn, or Python can't read it):
     the file kept as it is, marked at `def query`. A warehouse.py that already defines
     `connect` is left.
  2. **Workflow notebooks** written again (`_write_workflow_notebooks_again(upgrade,
     connection)`), names and step cells kept. **Decided: it now keeps the connection a
     notebook's setup cell gives** (`_connection_given`: the lines under 8.6's comment, in
     place of the placeholder), for every step from now on, so 8.7's rewrite won't drop it.
  3. **Admin notebooks** (`_admin_notebooks_as_8_6`): each text cell 8.6's (check_project's
     new text); check_references' `from warehouse import query` gains connect and the
     connect lines; run_tables gains 8.6's connecting cell after the path and loses
     `# from warehouse import query, execute`; remove gains `SCHEDULED_RUNS = []` under the
     names you gave, and its last cell.
  4. **Each Table notebook** (`tables/<stem>/<stem>.ipynb`): its first `from warehouse import
     X` becomes `from warehouse import connect, X` and CONNECT_LINES, filled as in 1. Its text
     cell is left: the Example projects' still say "- 1: the Project and your query."
  5. **Templates**: `saved_table` and `quality_checks` still as 8.2 to 8.5 wrote them
     (`TEMPLATES_BEFORE_8_6`) written again; one you changed marked (`TEMPLATE_MARK_8_6`).
  6. `add_what_start_makes()`: `scheduled_runs/`, the `scheduled_run` Template,
     `admin/scheduled_runs.ipynb`; a notebook it adds is filled as in 1.
  7. **Decided: records follow** (`_records_follow`): a file `promoted.json` or an open batch's
     `written.json` names, still as promote or convert wrote it before the step, gets its new
     hash, so check() doesn't call a connected prod copy "Edited by hand".
  8. **Decided: a notebook of yours** (any other .ipynb) importing from warehouse without
     connect is marked at that import; **a .py file is left**, as a module (a Run value's
     function in `building_blocks/run_values.py`) runs on its importing notebook's connection.
- **Decided: to_8_0 and to_8_2 write their own version's warehouse.py**
  (`WAREHOUSE_TEXT_8_0`, the new `WAREHOUSE_TEXT_8_2`), not today's, so to_8_6 finds 8.2's and
  reads its conn; before, a 7.2 or 8.1 Project got 8.6's text mid-chain and lost the Example
  connection.
- `tests/upgrade_from/8.5/`: the Example projects at `dd370f2f`, without Lineage pages (106
  files). The chain test runs 8.3, 8.4 and 8.5 to 8.6, its xfail lifted; `AWAITING_ITS_STEP`
  is empty; `GAINED_BY_HAND["8.6"]` as ticket 09 left it. **Decided: `LEFT_AS_IT_WAS["8.6"]`
  leaves out `finished/`**: a finished batch's record keeps the hash its notebook had when
  written, as 8.5's entry says of history.
- The journeys' `UNTIL_TO_8_6` marks are gone, and their fixture checks its hand edits again.
- `version.txt` says `sqlglot Composer 8.6`; `__init__`'s doctest, `project.upgrade`'s, how-to
  28's (and "here seven"), and the tests counting steps follow. `("project", "_hash")` is a
  listed private seam in `tests/repo/test_dead_code.py`.
- CHANGES.md's "To update from 8.5" and the README template's 8.5 bullet say what the step
  does (the three warehouse cases, the notebooks, the marks, the records).
- Tests: `tests/test_upgrades.py`'s 8.6 section (Example connection; your conn kept and marked;
  your own calls marked; a Workflow notebook's connection kept; remove's names kept; a
  notebook of yours marked and a module not; a promoted record following).
- D470 closed. Not run here: the `code-review` skill and the beginner reader (CHANGES.md, the
  README's Update bullet), for the caller.
