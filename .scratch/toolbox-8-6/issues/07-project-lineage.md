# The Project's lineage and its loops

Type: task
Status: resolved
Blocked by: 04
Size: L

## Question

Loops and tables two runs write made "evident in the lineage trace ... in the whole project"
(Q7), by hand only (Q17).

## Done when

- `project.export_project_lineage()` writes an HTML page and a Markdown twin in
  `admin/lineage/`: every Saved table as a box, an arrow from each table to each that reads
  it, each Scheduled run that writes a table named on it, a table more than one writes marked,
  a loop drawn red with its tables listed at the top. It builds each run (04) without sending,
  so it reads the warehouse only for Run values.
- `project.check()` reports a loop among the Project's tables, naming each table in it and
  the logic cell to mend, loading each table's logic; it changes nothing.
- `admin/scheduled_runs.ipynb`, made by `project.start()`, holds these calls, run by hand.
- Nothing here runs from a Scheduled run's notebook.

## Answer

Built 2026-11-09.

- `project.export_project_lineage()`, last in `__all__` and `PROJECT_NAMES`, gives a
  ProjectReport and writes `admin/lineage/<time>-project.html` and its Markdown twin,
  `<time>-project.md`; it changes no other file and adds no Admin log entry, as
  `export_lineage` adds none. Its work is in a new Toolbox file, `project_lineage.py` (in
  `toolbox_registry.PYTHON_FILES`). **Decided: a new file, not `lineage.py` or
  `scheduled_runs.py`**: tickets 05 and 06 change `scheduled_runs.py` alongside this one, and
  the page is a table-level drawing, not a Statement's column lineage.
- **Decided: each table is a box**: each Table folder the registry lists, each table a write
  of the Project writes (a Saved table with no Table folder, as a run's own write), and each
  table they read that the Project doesn't write, marked "read, not written here", so every
  arrow has a start. An arrow runs from each table a write reads to the table it writes; none
  from a table to itself, as a write adding to its own table reads it. Each table a
  Scheduled run writes, the writes its build adds included, names the run on its box, and a
  table more than one run writes is marked ⚠ (orange) and named in the report: shown, never
  refused. A loop is drawn red, boxes and the arrows that go round it, and listed at the
  top of both files and in the report.
- **Decided: the HTML page draws a static SVG, laid out in Python, and runs no script**: one
  column per step from the tables read, as the Statement lineage page lays out its boxes, in
  its colours, sizes and header key; it draws the same with scripts off and fetches nothing.
  The Markdown twin has a Mermaid chart, its loop boxes and arrows red by `classDef` and
  `linkStyle`, then a Tables list (what each is, what reads it, the runs writing it), each
  Scheduled run's Statements in order, headed as the build heads them, and a footer.
- **Building a run from outside its notebook: `project_lineage.built_run_of(root: Path,
  name: str, call: str) -> tuple[BuiltRun, str]`**, the built run and what the build
  printed, for ticket 08's `export_run_lineage` and `export_run_hive`. It runs, through
  `project.run_logic` as `load` runs a logic cell (the offline policy allows code to run only
  there), one module: the parameters cell (its defaults), **the imports only of each other
  code cell above `# scheduled`** (so the setup cell's `connect(...)` and anything else
  there never run), the `# scheduled` cell, and the Build cell's own `project.build_run(...)`
  call, its `run_values=` and `leave_out=` as written. **Decided: it runs from the run's
  folder (`contextlib.chdir`)**, as a scheduler does, so `build_run` finds the notebook and
  reads the parameters cell as it always does; stdout is caught. A Run value reads the
  warehouse through the connection of the calling notebook, `admin/scheduled_runs.ipynb`'s
  first cell. Refused: no notebook, no `# scheduled` cell (`notebooks.SCHEDULED`), a cell it
  runs that isn't Python yet (a `<...>` left), no cell after `# scheduled` calling
  `build_run`.
- A run that doesn't build, and a Table folder whose logic doesn't load, are shown on the page
  with the whole message, and named in the report on one line; Run value Warnings are
  silenced there, as a failed Run value changes no table read.
- `project.check()` reports a loop through `project_lineage.loop_lines`: each table in it,
  what of the loop it reads, and its notebook, whose `# logic` cell to mend; it changes
  nothing. **Decided: only this part of check() loads logic, once per Table folder**, a
  Table folder whose logic doesn't load passed over silently (the Workflows' lines name
  those). The loop is the one `in_order` refuses: `lineage.names_in_a_loop`, which shares
  `_needs` and `_placed` with `in_order`, refusing nothing.
- `admin/scheduled_runs.ipynb` (`ADMIN_NOTEBOOKS["scheduled_runs"]`): its text, the path,
  `from warehouse import connect` and the connect lines, `project.check()`, and
  `project.export_project_lineage()`. `start()` makes it, and run again in an older Project
  adds it. `tests/test_upgrades.py`'s `AWAITING_ITS_STEP` names it until ticket 12's Upgrade
  step. No Template or Scheduled run's notebook calls either.
- Private names made shared: `lineage.shortened`, `notebooks.first_line`,
  `project.one_line_message`.
- Tests: `tests/test_project_lineage.py`.

### The code review (2026-11-09)

- **A Table folder whose logic fails is no longer passed over silently by `check()`**: it is
  named on one line, "Passed over, as its logic doesn't load: mart.teams: name 'team_job'
  is not defined", the line the Project lineage's report gives, both through
  `project_lineage.passed_over_lines`. **Decided: not one whose logic isn't there yet**
  (`failing_logic_lines`): a logic cell not Python yet, as a Template's `<...>` left makes
  it, and a notebook not there, which check() already reports as registered but not there.
  Naming every new table still to fill in turned the all-clear line of the README and the
  how-tos into a line per table, for what blocks nothing the user can mend but by filling it
  in. This replaces "passed over silently" above.
- **A name a cell above `# scheduled` defines**: `built_run_of` still runs only those cells'
  imports, never `connect(...)` nor the user's lines. A NameError for a name one of them
  defines (a def, a class or an assignment, read by `ast`) is refused as a NameError naming
  it, saying only the imports above `# scheduled` are run and to move it into the
  `# scheduled` cell; a name defined nowhere is raised as Python raises it. Said in
  `built_run_of`'s and `export_project_lineage`'s docstrings, and CHANGES.md.
- **One way per job in `project_lineage.py`**: `NamedStatement`, a NamedTuple, for each
  (Statement, name) pair; `project_tables(registry, call) -> ProjectTables` (its writes,
  those passed over and the loop, `names_in_a_loop` called once there) for both `check()` and
  the page; `_reads_of_each_table`, the one walk over `tables_read`, which the arrows, the
  columns and `loop_lines` read; `_table_rows` (`TableRow`) and `_report_parts`
  (`ReportPart`) for what both files show; `_warnings_silenced`, the one
  `catch_warnings`. `ProjectLineage.written` became `reads`, by the table written.
- Names: `_kind_line` is `_kind_label`; `e = html.escape` is gone; a run's writers are kept
  with `dict.fromkeys`. Renamed: `project_writes` is `project_tables`; `loop_lines` takes
  the `ProjectTables`.
- From ticket 09 (by the coordinator): `admin/scheduled_runs.ipynb` gains `NEW_RUNS = []` and
  `project.new_scheduled_run(NEW_RUNS)`, with a sentence in its text cell.
