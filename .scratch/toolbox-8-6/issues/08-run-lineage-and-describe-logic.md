# A run's lineage and Hive, and describe_logic

Type: task
Status: resolved
Blocked by: 06
Size: M

## Question

One run's lineage and Hive written by hand into its folder (Q17, Q23); a Table notebook's
logic described for Copilot (Q25).

## Done when

- `project.export_run_lineage(name)` builds the run as its notebook's defaults give it and
  writes its lineage into `scheduled_runs/<name>/lineage/`, named by the time and the run.
- `project.export_run_hive(name)` writes the built Hive, in order, headed as the build prints
  it, into `scheduled_runs/<name>/<name>.hql`, to read, never to edit.
- `project.describe_logic(names)` prints each named table's logic functions: the signature
  with its hints, and its docstring's first line; a name with no Table folder refused, naming
  close ones.
- Each in `admin/scheduled_runs.ipynb`.

## Answer

Built 2026-11-09.

- Three public names, last in `project.__all__` and `PROJECT_NAMES`:
  `project.export_run_lineage(name: str | list[str]) -> ProjectReport`,
  `project.export_run_hive(name: str | list[str]) -> ProjectReport` and
  `project.describe_logic(names: str | list[str]) -> ProjectReport`. **Decided: each takes
  one name or a list**, as every Project action does since 8.0; the two run actions go
  through `_run_for_each_name`. Neither run action adds an Admin log entry or changes another
  file, as `export_lineage` and `export_hive` add none; `describe_logic` changes no file.
- Both run actions build the run through ticket 07's `project_lineage.built_run_of`: its
  parameters' defaults, the imports above its `# scheduled` cell, that cell, and its Build
  cell's call with its `run_values=` and `leave_out=`, from the run's folder, sending nothing.
  A run whose build is refused (a `<...>` left) is refused as the build refuses it. Their
  work is in `project_lineage.py`: `write_run_lineage` and `write_run_hive`.
- **Decided: a run's lineage is a Statement lineage, `export_lineage`'s page and twin, not the
  Project's table-level page**: every Statement the run sends, the writes its build adds and
  any its START_FROM default passes over included, column by column, titled "the Scheduled
  run <name>", into `scheduled_runs/<name>/lineage/<time>-<name>.html` and `.md`. Its footer
  names the call and each table's Session settings. A new `lineage.write_lineage(ordered,
  title, html_path, footer, made_by)` writes the two files, and `export_lineage` now calls
  it too; `lineage_footer` (was `_footer`) and `to_markdown` take `made_by=`.
- **Decided: a create, upkeep or Admin statement isn't drawn**, as `export_lineage` leaves an
  Admin statement out and refuses the others: the report names each ("Not drawn, as it makes
  no column from another: ..."), and a run with nothing to draw is refused.
- `<name>.hql`: **Decided: its header is comment lines, what it is ("to read, never to edit
  or to send", built again each run, its Run values worked out then), then what the build
  printed before its first Statement** (each parameter as used, the Run values `run_values=`
  gave, the Statements START_FROM passes over), taken from the build's printed text, so it
  stays what the build prints as tickets 05 and 06 change it. Then each Statement through a
  new `scheduled_runs.step_texts(built)`, which `_print_build` now prints too: its heading,
  `-- 3 of 7: mart.team_days (read by week_totals)`, a table's Session settings before its
  first write, and its Hive. It holds no time, so written again it is the same text.
  Shared for it: `running.hive_to_show` (was `_hive_to_show`; its frame may be None) and
  `running.hive_file_header`, the comment lines `export_hive` heads its file with.
- `describe_logic`: **Decided: it reads the logic cell and runs nothing**, so it needs no
  connection and works no Run value out. It reads the cell through `_checked_logic`, with
  `load`'s refusals (no notebook, no `# logic` cell, not Python yet, a `run_query` call), and
  gives each `def` at the cell's top level, so only the cell's own functions, not what it
  imports nor one defined inside another; classes are left out. Each is a Python stub, `def
  week_totals(week_start: datetime.date, day: str='mon') -> Statement:`, its arguments as
  `ast.unparse` writes them, hints, defaults and `*args` included, then its docstring.
  **Decided: the docstring's first sentence, on one line, not its first line**, since a
  docstring wraps its first sentence (the Example's `mart.team_days` does); "`... # no
  docstring`" when it has none. A line `# mart.team_days: project.load("mart.team_days"),
  from the # logic cell of <notebook>` heads each table, a blank line between tables. Every
  name is checked before any is described.
- A name refused: a new `project.check_there_is_one(root, kind, name, call)`, for a Table
  folder or a Scheduled run on disk, says "Did you mean a or b?" from `difflib`'s close
  matches (three at most), or else names each one there is.
- `admin/scheduled_runs.ipynb` (`ADMIN_NOTEBOOKS["scheduled_runs"]`) gains a cell of
  `RUNS = []` and `TABLES = []`, then `if RUNS: print(project.export_run_lineage(RUNS))`,
  `if RUNS: print(project.export_run_hive(RUNS))` and `if TABLES:
  print(project.describe_logic(TABLES))`, each list left empty passed over, as
  `admin/remove.ipynb`'s are; its text cell says what each does.
- CHANGES.md's `## 8.6` has a bullet; `project`'s docstring names the three and the run
  folder's `<name>.hql` and `lineage/`.
- For the merge with tickets 05 and 06: `_print_build`'s loop over the steps moved into
  `step_texts`; their changes to `_print_build` sit around it.
- Tests: `tests/test_run_lineage_and_describe_logic.py`.

### The code review (2026-11-09)

- **`<name>.hql`'s header from one source, not the build's printed text**: `BuiltRun` keeps
  `run_values_read_from` (what `run_values=` gave), and `scheduled_runs.lines_before_steps`
  gives what the build prints before its first Statement: `parameter_lines`, then the Run
  values given and the Statements START_FROM passes over, which `_print_build` prints and
  `write_run_hive` writes. So the header no longer follows a change in `_print_build`'s
  wording by parsing it, and nothing else the build printed slips in.
- `_export_run_lineage_one` and `_export_run_hive_one` are one `_export_run_one(name,
  function, write)`; `BUILT_AS` is `_built_as(it)`.
- Names: `_logic_described` is `_logic_function_lines`; `describe_logic`'s `listed` and
  `described` are `table_names` and `lines`; `shown` is `notebook`; `write_run_hive`'s
  `before` and `pieces` are `build_lines` and `texts`. `check_there_is_one` tests
  `isinstance(name, str)` once.
- `describe_logic` gives an `async def` at the cell's top level, as `async def ...`.
- **Answers the review on the first sentence**: `describe_logic` gives the docstring's first
  sentence, on one line, rather than its first line, as decided above: the Toolbox's own
  docstrings, and the Example's `mart.team_days`, wrap their first sentence, so a first line
  would cut it off.
- From ticket 09 (by the coordinator): the build's printout and `<name>.hql` show the Session
  setting "dynamic_partitions" once, after the heading of the first step that fills
  Partitions, and `built.run` now sends it there (was: first, before every step), both
  through `scheduled_runs._first_filling_partitions`; a write's Hive is shown without it
  (`running.statement_text`, which `hive_to_show` now uses). The scheduled_run Template's,
  `describe_logic`'s and a refusal's example call is
  `week_totals(FIRST_DAY, LAST_DAY)`, true of the Example's `mart.team_days`.
