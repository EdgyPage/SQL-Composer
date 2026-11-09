# project.new_scheduled_run and its Template

Type: task
Status: open
Blocked by: 01
Size: M

## Question

Where a Scheduled run lives and how it is made (map, "Scheduled runs", Where; Q5, Q18).

## Done when

- `project.new_scheduled_run(name)`, a Project action, makes
  `scheduled_runs/<name>/<name>.ipynb` from `admin/templates/scheduled_run.py`, and registers
  it (a new registry kind). Refused: a name taken, a name Python can't import, outside a
  Project.
- The Template's cells, top to bottom: `# parameters` (tagged `parameters` in the notebook's
  metadata), setup with `connect(...)`, `# scheduled` with `def statements():`, "Build", "Run",
  each with a comment saying what to fill in and what it does. Its parameters cell holds
  `START_FROM: str = ""` and one commented example parameter.
- `project.start()` makes `scheduled_runs/`; the Project tree in `project.py`'s docstring names
  it.
- `project.remove("<name>")` (remove.ipynb) removes one, as it removes a Table folder;
  `check()` reports a Scheduled run folder the registry doesn't list, and the reverse, with
  the call that mends each.
- `toolbox_registry` and the registry tests know the new kind.

## Answer
