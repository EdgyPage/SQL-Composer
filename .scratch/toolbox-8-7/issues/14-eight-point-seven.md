# 8.7: the Upgrade step and the raise

Type: task
Status: resolved
Blocked by: 04, 05, 06, 07, 08, 09, 10, 11, 12, 13
Size: M

## Question

The version the user named (Q1), and the Upgrade step every raise ships.

## Done when

- **`upgrades.to_8_7`, in `STEPS`:**
  - rewrites each `from sqlglot_composer import example_database` (and other import forms) in
    the Project's notebooks and `warehouse.py`, marking any it can't, with what to do;
  - makes `admin/workflows/schedule/`;
  - rewrites or replaces each mark earlier Upgrade steps leave that names the Example database
    as the connection, or `from sqlglot_composer import example_database` (`upgrades.py`'s
    `_CONN_GONE`, `_CONNECT_AS_CONN_WAS` and `_CONNECTED`), so an 8.5 Project upgraded straight
    to 8.7 is told only what 8.7 can do (drift D514);
    and empties `tests/conftest.py`'s `AWAITING_ITS_REWRITE` (ticket 12's Answer);
  - takes `NEW_RUNS` out of `admin/scheduled_runs.ipynb`, keeping the user's other cells;
  - loses none of the user's code.
- **The Example projects are frozen at 8.6** in `tests/upgrade_from/8.6/`, without their
  Lineage pages, from d1757e59, and `tests/test_upgrades.py` passes.
- `sqlglot_composer/version.txt` reads 8.7.
- **CHANGES.md's `## 8.7`** has "What's new" and "To update from 8.6", which names:
  - the Example database's leaving;
  - the docs' new place;
  - the schedule Workflow;
  - Hivevars;
  - the lineage pages' look;
  - a Conversion leaving out `SORT_ARRAY`'s `TRUE`, and keeping any other second argument
    with a `kept` finding (ticket 10);
  - the Copilot files' limit raised from 8,000 to 9,000 characters (the user's call, dev
    257d9724; `copilot/count_characters.py` allows 9,000);
  - every other change a user of 8.6 would notice, from each merged ticket's Answer.
- No drift item open.

## Answer

Built 2026-11-13, on dev at 87426a97, with dev's 257d9724 (the Copilot files' 9,000
characters) merged in.

- **`upgrades.to_8_7`, last in `STEPS`.** In order:
  - `_reword_warehouse_py`: each of the four pieces 8.6's warehouse.py said of the Example
    database (`_WAREHOUSE_WORDS_8_6`) is written as 8.7's, in a warehouse.py the user changed
    too; one still saying `connect(example_database)` is marked afterwards.
  - `_reword_8_6s_marks`: each `# UPGRADE 8.6:` mark the 8.6 Toolbox wrote that offered the
    Example database (`_SAID_BY_8_6`), in a `.py` file or a code cell, and each line of
    `admin/upgrade_8.6.md` saying so, is reworded as 8.7's Toolbox says it (drift D514).
  - `_add_the_schedule_workflow`: `add_what_start_makes`, which adds
    `admin/workflows/schedule/schedule.ipynb`, then fills in its `connect(...)` line with the
    lines the Project's other Workflow notebooks give.
  - `_take_new_runs_out`: `admin/scheduled_runs.ipynb` loses the cell 8.6 wrote, its
    `NEW_RUNS` named or not, every other cell kept, and its text cell is 8.7's.
  - `_rewrite_example_database_imports`: every `.py` file and code cell outside the Toolbox's
    folder and `admin/removed/`, through ticket 12's six forms (below), each line rewritten
    marked; code Python can't read has each line importing it marked.
  - Then the marks that wait for the rewrite: warehouse.py's line still naming the Example
    database, a cell of the user's still naming `NEW_RUNS`, and the schedule notebook's `NAME`
    for each run `NEW_RUNS` named whose notebook isn't made. Last, promote's and open batches'
    records follow each file changed, as 8.6's step does.
- **The six forms**, as tests hold each (`FORMS_8_6` in `tests/test_upgrades.py`):
  1. `from sqlglot_composer import example_database` is `import example_database`, a comment
     after it kept;
  2. among other names, on one line or in brackets, `import example_database` goes above, and
     the import keeps the others (the name's own line, or the name and its comma, taken out);
  3. `as demo` is `import example_database as demo`;
  4. `from sqlglot_composer.example_database import ...` is `from example_database import ...`;
  5. `import sqlglot_composer.example_database` is `import sqlglot_composer, example_database`
     (it bound both), and each `sqlglot_composer.example_database` in code is
     `example_database`; with only `import sqlglot_composer`, `import example_database` goes
     after it;
  6. a file using the bare name with `from sqlglot_composer import *` gains
     `import example_database` after the star import, and that line is marked. A name
     `example_database` the user binds themselves is left.
- **The marks.** Over an import a `connect(...)` line follows, as a setup cell's:
  `_EXAMPLE_CONNECTION_LEFT`, "8.7's Toolbox has no Example database, and your download has
  none, so this import fails there: delete it, and in the connect(...) below write your team's
  connection, such as connect(conn), imported as the comment above shows". Any other line:
  `_EXAMPLE_DATABASE_LEFT`; code it couldn't read: `_EXAMPLE_DATABASE_UNREAD`.
- **The 8.6 step's own texts** say nothing of importing the Example database: `CONN_GONE` and
  `_CONNECTED` are reworded, and `_CONNECT_AS_CONN_WAS` is gone, so an 8.5 Project upgraded
  straight to 8.7 is told only what 8.7 can do, and to_8_7 rewords the same texts in a Project
  the 8.6 Toolbox upgraded. `CONNECT_HERE` and `CONN_GONE` lose their underscore, since the
  tests read them.
- **`Upgrade.rewrite_cells`**, new: writes cells with `write_cell_text`, so a notebook keeps
  its tags and outputs. **`Upgrade.rewrite`** takes `said=`, as `rewrite_notebook` does.
- **The freeze.** `tests/upgrade_from/8.6/` is `git archive d1757e59 example_projects`,
  without its `lineage/` folders (112 files). `GAINED_BY_HAND["8.7"]["intermediate"]` holds
  the schedule notebook (from `AWAITING_ITS_STEP`, now empty) and the README.
  `tests/conftest.py`'s `AWAITING_ITS_REWRITE` is empty. `files_of` also leaves out a mark's
  line in a notebook's JSON (`UPGRADE_MARK_SOURCE_LINE`), since 8.7's marks are the first a
  frozen Example project's notebook gets. The chain from 8.3, 8.4, 8.5 and 8.6 passes, both
  Example projects.
- **The raise.** `version.txt` reads `sqlglot Composer 8.7`; `__init__.py`'s and
  `project.upgrade()`'s docstrings and how-to 28 say 8.7 (eight steps from 7.2); the pages,
  Copilot files, Example projects and snapshot are regenerated.
- **CHANGES.md's `## 8.7`** and the README's Update bullet for 8.6 to 8.7. The README names
  no `example_database`, as `tests/test_readme.py` holds.
- **Outside the ticket, kept small:** `tools/copilot_files.py`'s docstring and
  `tools/merge_copilot_files.py`'s header, re-wrapped, as dev's 257d9724 left each a line
  past ruff's 96. `.pytest_cache/memo/` was made in this worktree, git-ignored, which
  `tests/repo/test_pointers.py` wants since CLAUDE.md names it.
- **For the coordinator:** drift item D500 (the version item for ticket 10) is closed by this
  raise; I didn't edit `.scratch/drift.md`, as told.

**Decided:** form 1 is rewritten to `import example_database`, not to the line to fill in,
`# connect(your_connection)`. The frozen 8.6 Example projects must upgrade into dev's
current ones, which import it so (ticket 12), and dev's journeys run an upgraded Project. A
user's download has no such package, so the mark says the line fails there, to delete it, and
what to write in `connect(...)` instead. The beginner reader's design note (stop 3) leaves
the other way for the user to choose.

**Decided:** form 6 gains `import example_database` after the star import, one line marked,
not a mark on each use of the bare name as ticket 12's note proposed: it is the same rewrite
as form 1, and one mark asks one thing of the user where each use's would ask the same thing
many times.

**Decided:** the 8.6 step's texts are changed in place (D514's second way) and to_8_7 also
rewords them in a Project the 8.6 Toolbox upgraded (its first way), so both roads end at the
same words. A mark the user reworded is matched by exact text only, and left.

**Decided:** warehouse.py's words are rewritten piece by piece, not only where the file is
8.6's whole, so a warehouse.py the user changed (its calls renamed) loses the Example
database's name too.

**Decided:** the new schedule notebook is connected with the other Workflow notebooks' lines,
so a Project on its own connection gets it in the new notebook, and the starter Example
project upgrades into dev's. Where those lines name the Example database, the new notebook is
then marked as they are; its checklist line says so.

**Decided:** `admin/scheduled_runs.ipynb`'s text cell is 8.7's, even one the user edited, as
8.6's step wrote every admin notebook's text cell; the old notebook is kept in
`admin/removed/`.

**Decided:** a run `NEW_RUNS` named whose notebook isn't made is marked at the schedule
notebook's `NAME`, not written there, as 8.0 marked a Conversion to do again.

## Code review

Run 2026-11-13 against 87426a97 (diff read from 257d9724, dev's tip, merged), `review-standards`
and `review-spec` on Sonnet. Beginner reader:
[report](../reports/beginner-reader-ticket-14.md), its stops and what came of each at its end.

Standards, two hard findings, both fixed:

- `return cell, uses.package or uses.star` used `or` for a value: `_import_to_add_after` now
  tests each with `is not None`.
- `_reword_warehouse_py` overwrote `upgrade.changed[-1]` after `rewrite`: `Upgrade.rewrite`
  takes `said=` now, as `rewrite_notebook` does.

Its judgement calls:

- Names: `_left_said`, `_moved_by` and `_where_to_import` are `_mark_on_rewritten`,
  `_line_mover` and `_import_to_add_after`. Kept: `_chars`, `_segment_with`,
  `_example_uses` and `_example_imports_rewritten`, each with a docstring saying what it
  gives.
- The (line, indent) clump is `_ImportEnd`, a NamedTuple. The flag argument of
  `_end_of_import` became `_end_of_first(nodes, lines, matches)` with `_is_star_import` and
  `_is_package_import`. Kept: the dict of rewritten texts and marks, read in one place.
- Duplicated code: the replace loop is `_with_each_replaced`, used three times;
  `dict(texts)` is built once. Kept: the two warehouse.py functions each import `WAREHOUSE`,
  as every step's helper in upgrades.py does.
- Size: the import rewriting stays in upgrades.py. Each step's helpers live beside it there,
  and `toolbox_registry` would need a new file and its imports for one step's machinery.
- Speculative generality: the `as x` and submodule forms are ticket 12's forms 3 to 5,
  which this ticket's Done when asks for.
- `CONNECT_HERE`, `CONN_GONE` and `SCHEDULE_NOTEBOOK` are public: the tests read the first
  two (a private name read by a test would be a new seam in `tests/repo/test_dead_code.py`),
  and the third is a path like `PROJECT_VERSION`.

Spec:

- D500 open: the coordinator's to close, as above. Status and Answer: this section.
- Not asked for: the two re-wraps and the README bullet (above); the report is the
  Definition of done's.
- The text cell of `scheduled_runs.ipynb`, and form 6: decided above.
- Form 1 and the 8.6 texts: judged acceptable by the review, decided above.
