# The admin layout: databases.py, sent.csv, admin/workflows/, check() and do_next()

Type: task
Status: open
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
