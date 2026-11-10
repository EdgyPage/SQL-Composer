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
  1. **warehouse.py** (`_write_warehouse_as_8_6`), read with `ast`: its statements other than its
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
  3. **Admin notebooks** (`_write_admin_notebooks_as_8_6`): each text cell 8.6's (check_project's
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
  7. **Decided: records follow** (`_rehash_records`): a file `promoted.json` or an open batch's
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

### The code review (2026-11-09)

Standards and Spec axes on 3846ce9. The rule each mend follows: an Upgrade never loses your
code, and never leaves a Project that can't run without a `# UPGRADE 8.6:` mark saying why
and what to do. Mended in the commit after 3a30e3a, each test first:
- **Your comments kept.** `_your_statements` gives each statement of yours with the comment
  and blank lines above it (`_YourStatement`), and a comment of yours above the Toolbox's
  own statements, or at the end, as one with no lines of its own; each is kept where it sat.
  The comment 8.0 or 8.2 wrote above conn is the Toolbox's, untrue once conn is gone, and is
  left out (`_TOOLBOX_CONN_COMMENTS`). A comment of yours in a warehouse.py otherwise as
  start() wrote it makes it the kept case, not the Example case, so nothing is lost.
- **A `connect` of your own marked.** `_is_8_6s_connect` compares it, without its docstring,
  with `project.WAREHOUSE_TEXT`'s; yours is left and marked at `def connect`
  (`_CHECK_YOUR_CONNECT`). 8.6's is left unmarked, as before.
- **`from warehouse import conn` where conn is gone.** Decided: mark, not a kept `conn`, so
  warehouse.py stays exactly what start() writes. In the Example case only (in the kept case
  conn stays live; in the own-calls case the file is unchanged), `_mark_imports_of_conn`
  marks each line of yours, in a `.py` file or a notebook's code cell, that imports conn from
  warehouse (over several lines too) or reads `warehouse.conn` (`_CONN_GONE`). Code Python
  can't read is passed over, as `calls_to` passes it.
- **Toolbox notebooks' other import forms.** Aliased (`import query as q`) already matched.
  `_connected_cells` now connects a top-level import over several lines, parenthesised, or
  `import warehouse`, by adding `from warehouse import connect` and the connect lines after
  it (`_warehouse_imports`, by `ast`). One it still can't connect, inside a `try` or in a
  cell Python can't read, is marked: `_mark_notebooks_not_connecting` now marks every
  notebook that reaches the warehouse and doesn't connect, the Toolbox's included
  (`_CONNECT_HERE`). `_has_connect` reads a connect import over several lines too.
- **conn set in a `try` or an `if`.** `_names_set_at_module_level` reads the statements
  nested in a top-level one, never in a def or a class, so it is the kept case, marked above
  its first line.
- **D494.** `_CONNECTED` says "each Toolbox notebook".
- **Names.** `_write_warehouse_as_8_6`, `_your_statements`, `_function_named` (for
  `_defined`), `_names_set_at_module_level` and `_names_it_sets`,
  `_write_admin_notebooks_as_8_6`, `_run_tables_with_connecting_cell`, `_rehash_records`,
  `_mark_notebooks_not_connecting`; the locals `there`, `said`, `kept`, `found`, `given` and
  `written` renamed for what they hold. `CONNECT_LINES` and `CONNECT_PLACEHOLDER` are
  imported once, at the top (project_templates imports nothing). `_has_connect` is the one
  check that a notebook connects. Fewer hops for the connection: each part of the step
  connects with the line to fill in, and one pass at the end, `_fill_connect_lines`, fills
  each Toolbox notebook with the Example connection (kept in the archive first where no
  earlier part of the step wrote it); the connection reaches only that pass and the mark
  pass. `_YourStatement` and `_Record` are NamedTuples. Records now follow the marks too:
  `_rehash_records` runs last.
- **A Project with no warehouse.py** gets 8.6's (`upgrade.add`), since every notebook now
  imports connect from it.

Answered:
- **Admin notebooks' other text cells:** none. In 8.5 and 8.6 each admin notebook has one
  text cell, its first, which the step writes as 8.6's;
  `test_8_6_rewrites_each_admin_notebooks_one_text_cell` holds it, so a version that adds a
  second shows up there.
- **Templates' connect line:** already one rule. `_fill_connect_line` read only notebooks, so
  no Template, `scheduled_run` included, was filled; checked on the frozen 8.5 starter. Now
  `_fill_connect_lines` fills only Toolbox notebooks, and the Example-connection test holds
  `saved_table`, `quality_checks` and `scheduled_run` with their line to fill in, as start()
  writes them (ticket 01).
- Not run here: the beginner reader on the new marks and CHANGES.md's words, for the caller.
  The README template's Update bullet ("each notebook is connected to it") is the docs
  agent's to reword as D494 reworded `_CONNECTED`.
