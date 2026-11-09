# project.new_scheduled_run and its Template

Type: task
Status: resolved
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

Built 2026-11-09.

- `project.new_scheduled_run(name)`, a Project action, makes `scheduled_runs/<name>/<name>.ipynb`
  from `admin/templates/scheduled_run.py`, `<NAME>` filled in, registers it as the new registry
  kind `scheduled_run` (`project_files.SCHEDULED_RUN`, in `KINDS`) and logs it. Refused: a name
  taken, by a folder or by the registry; a name Python can't import, or one it keeps for
  itself; outside a Project; a missing Template. A list of names makes each, as the other
  actions do.
- **Decided: `project.remove_scheduled_run(name)`, not `project.remove(...)`.** The Toolbox has
  no `project.remove`: each kind has its own remover (`remove_table`, `remove_block`,
  `remove_conversion`), which `check()` names, so a Scheduled run has one too. `remove.ipynb`
  gains `SCHEDULED_RUNS = []` and its cell. Both names are last in `__all__` and in
  `PROJECT_NAMES`.
- `check()` reports a folder in `scheduled_runs/` the registry doesn't list, with
  `project.register("<name>")`, and one it lists that isn't there, with
  `project.remove_scheduled_run("<name>")`. A name with no dot now names a Building block and a
  Scheduled run to `register`, which adopts whichever is there. `FileKind.found` gives none for
  a folder a Project doesn't have yet, as an 8.5 Project has no `scheduled_runs/`.
- The Template (`project_templates.SCHEDULED_RUN`): a text cell (placeholders, Terms, Steps,
  what the build prints, Self-check), then `# parameters` (`START_FROM: str = ""`, a commented
  `RUN_DATE: datetime.date | None = None`), setup (`from warehouse import connect, execute,
  query` and `connect(<CONNECTION>)`, with warehouse.py's comment on a connection kept
  elsewhere), `# scheduled` (`def statements() -> dict[str, Statement]:`), Build and Run.
- **Decided: `write_notebook` tags a code cell whose first line is `# parameters` with
  `parameters`, papermill's tag** (`notebooks.PARAMETERS`, `PARAMETERS_TAG`), so a Template
  needs no tag syntax of its own. No other notebook the Toolbox writes has such a cell.
- **Decided: the Template isn't a Table notebook Template.** `_is_notebook_template` passes over
  `scheduled_run`, so `new_table(..., template="scheduled_run")` is refused and isn't offered.
- `project.start()` makes `scheduled_runs/`, and says so: "admin/, references/,
  building_blocks/, tables/, scheduled_runs/ and warehouse.py." Every docstring, how-to,
  the README and test showing that line changed with it. Run again in an older Project, it
  adds `scheduled_runs/` and the Template. The Project tree in `project.py`'s docstring names
  it. CONTEXT.md's Registry and Project action entries name a Scheduled run.
- `tests/test_upgrades.py`'s `AWAITING_ITS_STEP` leaves the Template and `remove.ipynb` out of
  the frozen Projects' comparison until ticket 12 writes 8.6's Upgrade step, which makes them:
  ticket 12 empties it.
- Tests: `tests/test_new_scheduled_run.py`; `test_project_files.py`, `test_project.py` and
  `test_toolbox_checks.py` know the kind and the names.
- Left for the docs (ticket 10): the README's own section on Scheduled runs (it only lists the
  Template), CHANGES.md, the Copilot files, and where a user calls `new_scheduled_run` from:
  no admin notebook makes one yet (ticket 08's `admin/scheduled_runs.ipynb` may).
