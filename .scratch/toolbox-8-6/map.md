# Toolbox 8.6: connect, and Scheduled runs

Label: wayfinder:map

The user (2026-11-09), with 8.5 on main: "Update warehouse.py to take in a connection, set that
as a global var, and then connection.query(hive) and connection.execute(hive). Fail if there is
no connection set." And: "I succesfully converted a mess of tables, but I want there to be a
place where I can schedule notebooks for execution by an external scheduler. I need to be able
to pull in the sql I need to run and run the final table in dependency order ... I am being told
to run the whole project and that's too much to schedule for one job." Grilled the same day in
three rounds, every question settled; the user named it 8.6 (Q2, "sure").

## Notes

### What is there today (8.5 at dd370f2f)

- `warehouse.py` sets `conn = example_database` when imported; `query` and `execute` pass the
  Hive to it. Every Toolbox notebook imports `from warehouse import query, execute`, about 20 in
  each Example project.
- `project.run_tables(tables=[...])` writes in lineage order (`lineage.in_order`), but only the
  tables named: it pulls in none they read. It passes over a Python step's table.
- A Table notebook's logic holds more than `write()`: `mart.team_days` has
  `week_totals(week_start, day)`, a weekly breakdown. A Scheduled run's Statements are "slight
  derivations, at best, of defined patterns and tables" (Q8).
- No lineage covers the whole Project; a loop is found only when `run_tables` runs.
- Guards refuse when `statement(...)` is composed; a Warning lets it through; Load limits are
  not Guards.

### connect (Q1, Q2)

- `warehouse.py` gains `connect(connection)`, which sets the module's one connection; `query`
  and `execute` call the connection's `query(hive)` and `execute(hive)`. Called before
  `connect`, each refuses: "No connection: call connect(...) first", naming the setup cell.
- Each notebook runs in its own process, so each Toolbox notebook's setup cell has a
  `connect(...)` line: the Example projects fill it with `example_database`; a new Project's is
  yours to fill. Each notebook, a Scheduled run among them, picks the account it runs as at its
  top, as credentials given at run time need (8.5's Q6b).
- Every Toolbox path that took `conn` as given (the how-tos, the journeys, the Workflow
  runner, `run_tables`' notebook) connects first.

### Scheduled runs (Q3 to Q16)

A **Scheduled run** (CONTEXT.md, 2026-11-09) is a notebook an outside scheduler runs top to
bottom, "explicitly in execution order" (Q4). "I want to separate building out the sql and
dependencies from actually running code" (Q3): building and running are separate cells.

- **Where**: `scheduled_runs/<name>/<name>.ipynb`, its folder laid out as a Table folder is,
  made by `project.new_scheduled_run("<name>")` from a Template in `admin/templates/`, and in
  the registry (Q5, Q18). `remove` removes one; `check()` reports one made by hand.
- **No dev/prod** (Q6): "I don't want the scheduled notebook to concern itself with dev/prod."
  It runs the tables it names, in whichever Database that is; the examples name dev tables.
- **The notebook, top to bottom** (Q13, Q21):
  1. `# parameters`, tagged `parameters` (papermill's tag): typed assignments with defaults,
     such as `RUN_DATE: datetime.date | None = None`, and `START_FROM: str = ""`. The user adds
     cells of their own beside it, such as a user ID ("I will make these cells myself").
  2. Setup: imports and `connect(...)`.
  3. `# scheduled`, the run's logic cell: `def statements():` gives the writes and SELECTs this
     run is for, from the Table notebooks' logic through `load(...)`, such as
     `load("mart.team_days").week_totals(WEEK)`, and Statements of its own. It may define Run
     values of its own (Q22), traced like any other, kept in the notebook.
  4. **Build**: `built = project.build_run(statements(), run_values={...}, leave_out=[...])`.
  5. **Run**: `results = built.run(query, execute)`.
- **Strong parameters** (Q13, "make sure passing in parameters is strong here in case I need to
  define days of interest or whatever"; Q21): before anything is built, each parameter is
  checked against its hint. A scheduler passes text, so `"2026-11-01"` given for a
  `datetime.date` is read as that date; a value that can't be is refused, naming the
  parameter; a parameter with no hint is refused; one the run needs left empty is refused. The
  build prints each parameter as used, first, so the scheduler's log holds what it ran with.
- **The build** (Q7, Q8, Q14, Q16):
  - the Hive is built fresh from the logic, so Run values are worked out now; the `.hql`
    beside a notebook is never what is sent. A Run value reading the warehouse needs
    `connect` before the build;
  - it adds the writes of every Project table the Statements read, all the way up, less
    `leave_out` (Q14: "I want to avoid that type of design, but let's build it in"); tables
    outside the Project are read, never written;
  - everything in lineage order, a loop refused;
  - `run_values={"period_end": END}` overrides Run values by name, reaching a `write()` that
    still takes nothing; the build names each it overrode. Arguments to logic functions are the
    other way in (Q16: both);
  - it prints the order and the Hive and sends nothing.
- **Guards only warn in the run's own cell** (Q13: "leave the guards as warnings, I don't
  necessarily want to make the library happy if I need to run some quick statements"; Q20): a
  Guard tripped by a Statement composed in the `# scheduled` cell becomes a Warning, and the
  build lists each one it let through, with its call. Statements loaded from a Table notebook
  keep their Guards. Load limits and refusals Hive would fail on anyway stay refusals.
- **The run** (Q8, Q10, Q11, Q15): each write through `execute`, each SELECT through `query`;
  `results` gives back each DataFrame by name, `results["week_totals"]`, and the user's own
  cells after it do what work needs. A Python step's table is written, its rows built through
  `query` and saved through `execute`. It stops at the first that fails, raising, so the
  scheduler sees the notebook fail, and prints the parameter to rerun from it,
  `START_FROM = "mart.team_days"`; a plain rerun is safe too.
- **Two runs may write the same table** (Q7: "I have ways to schedule runs so they don't step
  over each other and I should plan for that in my own designs of statements"). It is shown,
  never refused.
- **Nothing written per execution** (Q17, Q24): no lineage, no record file; the scheduler's
  saved output is the record, as many schedulers run a copy of the notebook elsewhere. An
  Admin statement is logged by `run_execute`, as anywhere.

### By hand, never on a schedule (Q17, Q23, Q25)

"make the lineage tracking a manual process. I don't want to have this happen every time a
scheduled run executes. waste of compute." One admin notebook, `admin/scheduled_runs.ipynb`:

- `project.export_project_lineage()`: every Saved table, which Scheduled runs write each, a
  table more than one writes marked, and any loop drawn red.
- `project.export_run_lineage(name)` and `project.export_run_hive(name)`: one run's lineage and
  its built Hive, `<name>.hql`, into its folder.
- `project.check()` reports a loop among the Project's tables, loading each table's logic.
- `project.describe_logic([...])`: each logic function with its signature and its docstring's
  first line, to paste under Copilot file 18.

### Copilot file 18 (Q12)

Its own file, at most 8,000 characters: filling in a Scheduled run's Template from a
`describe_logic` paste, the parameters cell, `build_run`'s keywords and a worked example.

### The version

8.6, named by the user (Q2). Its Upgrade adds `connect` to `warehouse.py` and marks the old
`conn = ...` line to move into a `connect(...)` call, never rewriting the user's connection
code; adds a `connect(...)` line to each Toolbox notebook's setup cell; makes
`scheduled_runs/`, the Template and `admin/scheduled_runs.ipynb`; and freezes the Example
projects at 8.5 in `tests/upgrade_from/8.5/`.

### Words

- **Scheduled run** (CONTEXT.md, 2026-11-09). _Avoid_: job, DAG, pipeline, schedule.
- **Parameter** (CONTEXT.md, 2026-11-09, D469): a value the scheduler passes into a Scheduled
  run's parameters cell, read by its hint. _Avoid_: argument, variable, input, setting.
- **Warehouse**, **Project** and **Guard** changed with it: the connection given by `connect`
  in each notebook; the Project's folder of Scheduled runs; a Guard only warning in a Scheduled
  run's own cell.
- Not new words: "Build" and "Run" are cells' headings.

## Tickets

- [01 connect](issues/01-connect.md)
- [02 project.new_scheduled_run and its Template](issues/02-new-scheduled-run.md)
- [03 The parameters cell](issues/03-parameters.md)
- [04 project.build_run](issues/04-build-run.md)
- [05 Guards only warn in the run's own cell](issues/05-guards-warn.md)
- [06 built.run](issues/06-run.md)
- [07 The Project's lineage and its loops](issues/07-project-lineage.md)
- [08 A run's lineage and Hive, and describe_logic](issues/08-run-lineage-and-describe-logic.md)
- [09 A Scheduled run in the Example project, and its journey](issues/09-example-and-journey.md)
- [10 The docs and Copilot file 18](issues/10-the-docs.md)
- [11 The usability round](issues/11-the-usability-round.md)
- [12 8.6: the Upgrade step and the raise](issues/12-eight-point-six.md)

One at a time, by number, the user's habit. The real dependencies are in each ticket's
`Blocked by:`.

## Records this changes

- `sqlglot_composer/`: `project.py` (`WAREHOUSE_TEXT`, 01; 02, 04, 06 to 08), a new
  `scheduled_runs.py` (03, 04, 06), `lineage.py` (07, 08), `refusals.py` and `checks.py` (05),
  `project_files.py` and the Templates (02), `workflows.py` (01's setup cells), `upgrades.py`
  and `version.txt` (12), `public.py`.
- `tools/toolbox_registry.py` (the new file), `tools/example_project.py` (09),
  `tools/copilot_sources/` (10), `tools/usability_scenario_files.py` (11).
- `tests/journeys/` (09), `tests/test_upgrades.py` (12), the how-tos' and journeys' setup (01).
- CONTEXT.md: Scheduled run, Warehouse, Project, Guard (already, 2026-11-09).
- CLAUDE.md: this map; a Project's `scheduled_runs/` (10). CHANGES.md's `## 8.6`.
- The README, the how-tos, `docs/workflows.md`, the Copilot files (10).

## Decisions so far

## Not yet specified

## Out of scope

- A dev or prod setting in a Scheduled run (Q6).
- Refusing a table two Scheduled runs write, or ordering runs against each other (Q7): the
  user's scheduler and design.
- Lineage, Hive files or a record written when a Scheduled run executes (Q17, Q24).
- The Toolbox saving query results to files (Q15).
- A connection per Database, or the Toolbox handling credentials (8.5's Q11).
- `write()` taking arguments (Q16).
