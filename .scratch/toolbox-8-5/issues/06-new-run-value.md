# project.new_run_value

Type: task
Status: resolved
Blocked by: 02
Size: S

## Question

Every W7 run wrote `building_blocks/run_values.py` by hand and registered it from no cell (map,
"Fewer Decisions written out").

## Done when

- `project.new_run_value(name, *, latest_partition)`: `latest_partition="ops.job_runs.dt"`
  writes `def <name>() -> datetime.date` returning `latest_partition(<table>.<column>, query)`
  into `building_blocks/run_values.py`, with its imports (made if missing), and registers the
  file, as `new_block` does. Its report gives the import line to put at the top of the
  decisions cell.
- Refused: a name already in the file; a table with no Table reference (naming the references
  Workflow); a column not one of its partition columns.
- Another kind of function is the file to edit, which the docstring and how-to 09 say.
- The convert notebook's decisions cell comment names it; no cell of its own (8.4's ticket 14).
- The journey (01) uses it in place of writing the file, its action count falling.

## Answer
Built 2026-11-05.

- `project.new_run_value(name, *, latest_partition)`, a Project action, last in `__all__` and
  in `tests/repo/test_toolbox_checks.py`'s `PROJECT_NAMES`. `latest_partition="ops.job_runs.dt"`
  writes `def <name>() -> datetime.date` (`-> int` for a whole-number column, such as
  `year INT`, as `latest_partition` gives a number there) returning
  `latest_partition(job_runs.dt, query)` into `building_blocks/run_values.py`, with only the
  imports the file lacks, under its own imports. A missing file is made with a module docstring
  saying any other kind of function is written there by hand. It registers the file (once, as a
  Building block), logs the call, and its report ends with the import line for the top of the
  decisions cell. It never touches the warehouse.
- Refused: a name the file has already (a function, class, assignment or import); a table with
  no Table reference, naming the references Workflow's notebook; a column that isn't one of its
  partition columns, naming them (a table with none, too); a `latest_partition=` that isn't
  `db.table.column`; a name Python can't import; a file that isn't Python; an import it needs
  whose name the file has for another thing. A table whose short name the file has for another
  thing is imported by its file's name, `... import job_runs as ops__job_runs`.
- **Decided: run again as it was, it changes nothing.** The decisions cell comment
  (`workflows.DECISIONS_CELL`) says to write the call at the top of the decisions cell, the
  import under it, and run the cell once. A cell run again, as a step-by-step run or a mended
  answer does, would otherwise be refused, so the same call finding the very function it writes
  reports "holds period_end already ... nothing changed" with the import line; any other use
  of the name is refused as the ticket says. No cell of its own.
- The docstring's worked example shows the whole file it writes; its last paragraph says any
  other kind of Run value is a function you write in the file. How-to 09 is ticket 11's.
- The runner journey types `project.new_run_value(...)` above the import in the decisions cell,
  in place of saving `run_values.py` by hand: **13** actions, from 14; the user's batch
  converted and promoted, **19**, from 20 (`KNOWN_ACTIONS`). The other two Run value journeys
  still save the file by hand, as a hand-written Run value is still a path.
- Tests: `tests/test_new_run_value.py`; `tests/test_docstrings.py -k new_run_value`.
- Left for ticket 11 and the regenerated files: the README, how-to 09, CHANGES.md, the Copilot
  files, `examples.html` and the Example projects' convert notebooks, whose decisions cell
  comment changed.
