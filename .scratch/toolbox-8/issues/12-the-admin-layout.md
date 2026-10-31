# The admin layout: databases.py, sent.csv, admin/workflows/, check() and do_next()

Type: task
Status: resolved
Blocked by: 11
Size: L

## Question

The user (2026-10-30): "truly workflow agnostic things can sit in admin with workflow specific
stuff inside workflow folders", each Workflow written in code with its docs "aligned to code".
The map's "The Project's layout" holds the design.

## Done when

- `start()` writes `admin/databases.py` (`DEV` and `PROD`, each `<...>` to fill in) and
  `admin/sent.csv`; `run_tables` and the notebooks' `create()` and `write()` append a row to it
  for each send. The check names `databases.py` until it is filled in.
- `admin/` holds only the agnostic notebooks (the check, `run_tables`, the Reference sheet,
  `check_references`, one `remove`), and `admin/workflows/<name>/` a notebook per Workflow,
  generated from its step list: one cell per step, its call written out with the Project's own
  names where they are known, never a `"your_name"` to edit, and a `do_next()` cell.
- Each Workflow's how-to is generated from the same list, and a test holds both to it.
- `project.check()` reports each Workflow instance's next step, and the first step not done in a
  Workflow that has no instances; `project.do_next()` runs every next step that changes only
  files, in order, and stops at the first permission or decision, naming it as a call ready to
  run. It never sends anything.
- Each step in `sqlglot_composer/workflows.py` gains the function that says whether it is done,
  read from the Project's files (moved here from ticket 10). A Warehouse step is done when its
  row is in `sent.csv`.
- CONTEXT.md gains **Dev Database** and **Prod Database**; the Project, Project action and
  Registry entries say where things now live.
- The graph's fiddling count falls for every Workflow whose commented-out calls are gone.

## Answer

Built 2026-10-31.

- **The layout.** `start()` writes `admin/databases.py` (`DEV` and `PROD`, each `<...>`),
  `admin/sent.csv` (its header: time, kind, tables, script) and `admin/workflows/<name>/<name>.ipynb`
  for each of the six Workflows. `admin/` keeps only the agnostic notebooks: `check_project`
  (with a `project.do_next()` cell), `check_references`, `refresh_reference_sheet`,
  `run_tables`, `new_block`, and one `remove`, whose first cell names the TABLES, REFERENCES,
  BLOCKS and CONVERSIONS to archive.
- **A Workflow's notebook** is generated from its step list (`workflows.notebook_cells`): its
  about, the path lines (`parents[2]`), a first cell of inputs, then a markdown and a code cell
  per step, each call reading the inputs by name, so no `"your_name"` is left. `given_inputs`
  reads that first cell with `ast.literal_eval`; a Workflow is started once one input is filled.
- **Done functions.** Each step in `workflows.py` has one, read from the Project's files
  (`every_table_folder_made`, `every_reference_written`, `every_reference_filled_in`,
  `every_logic_written`, `every_table_written`, `reference_sheet_is_fresh`,
  `project_is_current`, `no_upgrade_mark_left`, `every_change_sent`); a Warehouse step is done
  when its tables have a `write` row in `sent.csv`. File steps that run themselves carry a run
  function too (`make_table_folders`, `refresh_the_sheet`, `upgrade_the_project`).
- **sent.csv.** `run_execute` adds a row, through `unchecked.record_sent`, for each send from
  a Project that has the file, so `run_tables` and a notebook's `create()` and `write()` are
  covered in one place.
- **`project.check()`** ends with the next step of each started Workflow, naming its notebook,
  its number, its kind and its call; **`project.do_next(workflow=None)`** runs file steps in
  order, stopping at the first that is the user's, and never sends.
- **The version raised to 8.0 here**, not at ticket 20: 7.2 Projects keep the one-action
  notebooks, so the Upgrade test needed 8.0's step now. `to_8_0` archives the six retired
  notebooks, writes `new_block` and `check_project` again (each kept first), replaces a
  warehouse.py still as 7.2 wrote it, and adds what `start()` makes. `tests/upgrade_from/7.2/`
  freezes the Example projects as 7.2 left them; `GAINED_BY_HAND` keeps only the two READMEs.
- **CONTEXT.md** gains Dev Database and Prod Database; Project and Project action say where
  things live. CHANGES.md's 8.0 has a Workflows section and "To update from 7.2".
- **Fiddling** fell from 17 to 12: new_table, references and change_a_saved_table 0, convert 9.

Settled differently from Done when, each recorded:
- **An unstarted Workflow is not listed by `check()`.** Each has only its input cell to show
  until its first cell names something, so listing six first steps on every check was noise.
  `check_project.ipynb` and the README say where the Workflows are.
- **`check()` naming `databases.py` until it is filled in moves to ticket 13**, the first that
  reads `DEV`: every how-to's check output would otherwise change twice.
- **Each Workflow's how-to generated from the step list moves to ticket 19**, which rewrites the
  how-tos around the Workflows; `docs/workflows.md` is generated from the same list meanwhile.
- **conversions/ stays in `admin/`** until ticket 13 makes a Conversion read n scripts.
