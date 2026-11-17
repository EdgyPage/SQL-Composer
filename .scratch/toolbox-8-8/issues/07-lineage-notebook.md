# admin/lineage.ipynb

Type: task
Status: resolved
Blocked by: 03, 05
Size: S

## Question

Where the user records and asks for the difference by hand (Q15).

## Done when

- **`project.start()` writes `admin/lineage.ipynb`**, owned by no one Workflow, like
  `check_project.ipynb`:
  1. a text cell saying what the Lineage state and the Lineage difference are, and that each
     Project action and each Table notebook's cell 5 records already;
  2. a cell finding the Project, as the other admin notebooks do;
  3. `project.record_lineage_state()`;
  4. `SINCE = None` and `TABLES = None`, each with a comment of what it takes, then
     `project.export_lineage_difference(since=SINCE, tables=TABLES)`.
- It needs no `connect(...)` (Q6), and says so.
- `admin/scheduled_runs.ipynb` is unchanged.
- The Example projects hold it; `project.py`'s Project layout docstring and CLAUDE.md's "A
  Project's admin folder" name it and `admin/lineage/lineage_state.csv`.

## Answer

Built 2026-11-17, from dev's 973594c2 (tickets 01 to 06 and their merge fixes).

- **`project.ADMIN_NOTEBOOKS["lineage"]`**, so `project.start()` writes
  `admin/lineage.ipynb` (`project.LINEAGE_NOTEBOOK`) as it writes `check_project.ipynb`,
  through `_add_admin_files`, and a completing `start()` adds it to a Project that lacks it.
  Its cells are `project.admin_notebook_cells("lineage")`, which ticket 10's Upgrade writes:
  1. a text cell: what the Lineage state and the Lineage difference are, that each Project
     action changing a table or Table reference and each Table notebook's cell 5 record already,
     what SINCE and TABLES take, and that the notebook needs no `connect(...)`;
  2. the cell putting the Project on Python's path, as every admin notebook's;
  3. `project.record_lineage_state()  # after a change no Project action or cell 5 made`;
  4. `SINCE = None` and `TABLES = None`, each with its comment, then
     `project.export_lineage_difference(since=SINCE, tables=TABLES)`.
- **check() asks for a first recording only when there is a column to record** (a fix to
  ticket 04, found here): once the notebook is there, a Project whose only table still holds
  new_table's `<...>` has nothing that builds, so the first recording writes only the CSV's
  header, and check() would have asked for one again after it, each time.
  `effective_logic.project_logic` is worked out only in that case, before any recording.
  With that, no README step, how-to or Example project shows "No Lineage state yet": every
  Project action that makes a table, run or reference records, as `register` does.
- `project.py`'s layout docstring names `admin/lineage.ipynb`, and CLAUDE.md's "A Project's
  admin folder" names it and `admin/lineage/lineage_state.csv`.
- The Example projects hold it; the pages built from them, the how-to page (each `start()`
  writing one file more) and the Copilot files are written again.
- **Tests:** `tests/test_lineage_notebook.py`, 2: start() writes the notebook with its cells,
  and its cells, run as Jupyter runs them with no connection, record an Example project's
  Building block change and write the difference; `tests/test_check_unrecorded.py` gains a
  table still to fill in asking for no first recording; `tests/test_project.py`'s admin
  notebooks name it, and its registry-read count leaves out the Lineage state's own reads.
