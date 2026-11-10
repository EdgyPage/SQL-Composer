# The docs and Copilot file 18

Type: task
Status: resolved
Blocked by: 09
Size: L

## Question

Everything a user reads says connect and Scheduled runs.

## Done when

- The README template: connect in its setup, and a Scheduled runs section.
- A how-to, "Schedule a run", and the how-tos naming `conn` changed to connect.
- `docs/workflows.md`, CHANGES.md's `## 8.6` (what's new; to update from 8.5).
- Copilot file 18, `18_scheduled_runs.txt`, at most 8,000 characters: the Template, a
  `describe_logic` paste, `build_run`'s keywords, the parameters cell's hints, a worked example
  run in tests; `00_start_here.txt` lists it; file 01 and any naming `conn` say connect.
- CLAUDE.md's Project admin folder paragraph names `scheduled_runs/`.
- The beginner reader runs; its stops are mended or answered here.

## Answer

Built 2026-11-09.

- **The README template**: step 1's connect already said connect (ticket 01); its block now
  imports `connect`. **Decided: Scheduled runs are a reference section, `## Scheduled runs`,
  after The Workflows, not a tenth tutorial step**: the numbered steps are the Getting started
  how-tos, and a Scheduled run is Intermediate. It gives what one is, its five cells, eight
  steps to make one (the notebook, `describe_logic`, the parameters and their hints and
  refusals, connect, `statements()` and the three ways a value goes in, the build and what it
  adds, `run_values=` and `leave_out=`, the run, START_FROM and failure, scheduling with
  papermill), Guards only warning in the run's own cell and why, the by-hand cells of
  `admin/scheduled_runs.ipynb`, `remove_scheduled_run`, and the how-to's link. "How to read
  this page" names it; the file list gains `admin/lineage/` and `admin/scheduled_runs.ipynb`
  (D483) and the run's `.hql` and `lineage/` (D487); the Example projects section names
  `weekly_team`; the Copilot section names file 18; Update gains an 8.5 bullet, as ticket 12's
  spec says the Upgrade will do.
- **How-to 31, "Schedule a run"** (Intermediate), run in tests as the others: in a copy of the
  Intermediate Example project, `describe_logic("mart.team_days")`, `new_scheduled_run
  ("team_day")`, the notebook filled in (its text cell cut down), the build from its folder
  with `READ_DAY` passed as text, `built.run` on the Example database with
  `results["team_day"]`, scheduling with papermill and START_FROM, and `export_run_hive`.
  **Decided: the run writes `mart.team_days` (the build adding its two tables) and reads
  `team_day_from_job_events`**, since the Example database holds no mart table to SELECT from;
  the how-to says so. **Decided: the notebook is shown as the user fills it in, its code
  cells' comments copied from the Template as generated today**; the after-edit file isn't
  checked against the Template, so a Template change after the merge (the parallel ticket
  07/08 mend of its example comment) leaves the how-to's copy of the comments to read again.
  How-to 01's file list gains every `scheduled_runs/` path, `admin/lineage/` and
  `remove_scheduled_run`; how-to 26 a Common mistake on a Scheduled run and `rows=`. No how-to
  named `conn` but as a connection file's import (ticket 01 changed them).
- **docs/workflows.md** (from `tools/workflow_graph.py`'s heading): each Workflow notebook
  connects at its top, and a Scheduled run is not a Workflow, with its Build and Run cells.
- **CHANGES.md's 8.6**: the summary names Scheduled runs; "To update from 8.5" (copy in, run
  `project.upgrade()`, warehouse.py's `connect` with the `conn = ...` line kept and marked, each
  notebook's `connect(...)` line, what you fill in by hand, what is made); bullets for the docs
  and Copilot file 18. Dev's NEXT_DAY bullet (c2697445) merged in.
- **Copilot file 18, `18_scheduled_runs.txt`, 7,313 characters** (7,469 with Windows line
  breaks): the parameters cell's hints, a `describe_logic` paste, `statements()`, the Build
  cell's `run_values=` and `leave_out=`, START_FROM, and two worked examples, `weekly_team`'s
  cells from a paste and a Statement of its own; the second and the parameters block run on
  the Example database in `tests/test_copilot_files.py`, the first, calling `build_run`, is read
  as every Project action's block is. **Decided: it holds no `{always}` block**, as files 13
  to 17 don't: it leaves a Statement of its own to file 03. `00_start_here.txt` lists it and
  gains a Decision rule; `statements` is one of the user's own calls in the test; the merge
  takes it in by its glob. File 01 already said connect; no Copilot file names `conn`.
- **`tools/copilot_eval.py`'s stand-ins are connect-shaped**: the stand-in Project's
  warehouse.py has `connect` and sends through `_connection`, connected to the Example
  database as a setup cell would; a Workflow task's warehouse.py is the same, None until
  `NOTEBOOK_IMPORTS`, the cells above the names cell, run `connect(conn)` with the task's
  warehouse.
- CLAUDE.md's admin folder paragraph names `scheduled_runs.ipynb`, `scheduled_runs/<name>/` and
  `admin/lineage/`. CONTEXT.md gains **Project lineage**, and **Lineage** says it is a
  Statement's (D485). `project.py`'s module docstring names build_run, the three exports and
  check as reading the warehouse only through a Run value, check()'s and export_run_hive's
  docstrings say so (D484, D486).
- **The beginner reader** ([report](../reports/beginner-reader-ticket-10.md)), 22 stops.
  Mended here: the parameters don't reach the writes the build adds (its costliest, stops 8
  and 22): the how-to's parameter renamed `READ_DAY`, apart from team_days' own `DAY`, with
  rules and a Common mistake, and the README and file 18 say a parameter reaches only what
  `statements()` passes it to; the three ways a value goes in (stops 12, 20), in README step 5
  and 6 and file 18; why Guards only warn there (14), in the README and the how-to; the
  README's connect block's import (18), "a cell that sets a user ID" (19), where the `conn`
  line moves (21, and CHANGES.md); "paste after file 18" (17); in the how-to, a write's key,
  `str(READ_DAY)` and why the SELECT reads ops tables; JupyterLab's tags (9), in the how-to.
  The SET lines printed before each write but sent once is mended by tickets 07 and 08's
  review (17d62493): the build prints "dynamic_partitions" once, as the run sends it, and the
  how-to shows that. Answered, not mended here, being code or files another ticket owns:
  - the Template's `week_totals(WEEK)` (3): tickets 07 and 08's review made it
    `week_totals(FIRST_DAY, LAST_DAY)`, which the README now matches; its `run_value` import
    (6) and weekly_team's `<RESULT_NAME>`/`RUN_DATE` comments (7) are the Template's and the
    Example's, left for ticket 11's round;
  - WAREHOUSE_TEXT's "You pick which one sends" (1) and connect's "change the functions in
    warehouse.py" against the README's "you fill in nothing" (2): left for ticket 11's round,
    as warehouse.py's text is an Upgrade's to rewrite (ticket 12);
  - "Tag the cell ... View, then Cell Toolbar" (9) in the parameters' refusal, build_run's
    docstring example's imports (11) and wording (12, 13), export_project_lineage's example
    (15) and remove_scheduled_run's comment (16): docstrings and refusals of tickets 03 to 08,
    left for their code review's mend or ticket 11; (10) is how it works, as ticket 03 decided;
  - the 8.5 in version.txt and file 18's title (21): ticket 12 raises it.
- **Merged with dev at 17d62493** (tickets 07 and 08's review): the README's steps make a run
  and describe logic through `admin/scheduled_runs.ipynb`'s `NEW_RUNS` and `TABLES` cells,
  its by-hand list names `NEW_RUNS`, check()'s failing Table folders and that only the imports
  above `# scheduled` run in an export; how-to 31 names the two cells and shows
  "dynamic_partitions" printed and sent once; check()'s docstring keeps both mends.
- **Drift opened on 17d6249, fixed here**: D488, the docstrings, the refusal and CHANGES.md
  saying only the imports above `# scheduled` run, now that the `# parameters` cell runs whole
  and of the others only the imports, as `built_run_of` says; D489, **decided: check() passes
  over a logic cell's SyntaxError only when Python stops at a line holding a `<...>`**
  (`project_lineage._is_logic_not_there_yet`, through `project.PLACEHOLDER`), so a typo is
  named on the "Passed over" line, tested by
  `test_check_names_a_table_whose_logic_has_a_typo_python_cant_read`; D490, the weekly_team
  source's comment, `week_totals(FIRST_DAY, LAST_DAY)`, the Example regenerated.
- Tests: the whole suite passes on the merge with dev at 621cae34 (exit 0), its snapshot
  written again.
- Left: the code-review skill (for the caller); ticket 12, the Upgrade the README and
  CHANGES.md describe; the stops above answered for tickets 07, 08, 11 and 12.

### Cleanup before the round (2026-11-09)

On dev at 3846ce9 (ticket 12 merged), before ticket 11's round. Behaviour unchanged: only
texts a user reads, the Example projects regenerated from them.

- **D491**: the README's `RUNS` bullet says the `# parameters` cell runs whole and, of the
  other cells above `# scheduled`, only their imports, never their `connect(...)`, since
  `admin/scheduled_runs.ipynb`'s first cell connects for them, nor a line of yours.
- **D492**: README step 7: a plain run again is safe when each write is an
  `INSERT_OVERWRITE`, printed as `INSERT OVERWRITE TABLE`, which replaces its Partitions or the
  whole table; a run holding an `INSERT_INTO`, printed `INSERT INTO TABLE`, runs again only
  with the `START_FROM` it printed. How-to 31 says "here, each write", pointing at the lines
  its build printed, and the same of `INSERT_INTO`.
- **D493**: the section opens "one notebook that writes the tables it needs".
- **Stop 1** (WAREHOUSE_TEXT's "You pick which one sends"): it says which of query and
  execute, and that a Scheduled run's Run cell, `built.run(query, execute)`, picks the same way.
- **Stop 2** (connect's refusal against "you fill in nothing"): warehouse.py's text says you
  edit nothing there unless your connection names its calls another way, and then what to
  change, as the refusal does; the README's `warehouse.py` bullet says the same. The refusal
  is unchanged.
- **Stop 6** (the Template's `run_value`): its `# scheduled` comment says how a Run value goes
  in, `week_totals(run_value(week_first_day), ...)`, and to import `run_value` from
  sqlglot_composer there; weekly_team's copy of the comment matches. **Decided: no import added
  to the Template's setup cell**, which would be an unused import in most runs.
- **Stop 7** (weekly_team's `<RESULT_NAME>` and `RUN_DATE`): the Template's step 5 and Run
  comment say `results` holds each SELECT's rows by the name `statements()` gives it, such as
  `results["week_totals"]`, with no `<...>` in a code cell's comment; its Build comment says
  RUN_DATE is a parameter of yours and what `leave_out=` leaves out, so weekly_team, which
  keeps the Template's Build and Run cells, holds no leftover `<...>` and names no parameter
  it lacks. **Decided: weekly_team doesn't fill its own Build and Run cells**: the journey
  counts each cell filled as an action the user takes, and a Build and Run cell as written
  need none. Its text cell is still the Template's, as a user's is (stop 14 of the second
  read, answered: how-to 31 says you may cut it down). Stops 12 and 13 of the second read,
  on weekly_team's own Build and Run comments, went with those cells.
- **Stop 9** (the untagged parameters refusal's "View, then Cell Toolbar"): its fix says the
  tag is the word papermill looks for, and how to add it in JupyterLab (the Property
  Inspector) and in VS Code (Add Cell Tag), then to save.
- **Stops 11, 12, 13** (build_run's docstring): its example imports what it uses (`FROM`,
  `SELECT`, `WHERE`, `equals`, `statement`, and `job_runs` from the Example database), its
  comments say what `START_FROM = ""` and `statements` stand in for; `run_values=` "in place of
  calling the function, in every Statement built, the writes the build adds among them",
  whose `write()` takes no arguments; `leave_out=` leaves out that table's write and each
  added only because it reads it (the README's step 6 says the same).
- **Stop 15** (export_project_lineage's example): a comment says the new run's `<...>` aren't
  filled in, and a paragraph says how cell 4 and its line 13 are counted and what a filled-in
  run gives. The line is 13 now, the Template's comment a line longer.
- **Stop 16** (remove_scheduled_run's comment): moved off the call into a sentence saying the
  `...` is the time the removal ran.
- **The Table notebooks' "The code cells"**: "1 the Project and your query, connected by
  `connect(...)`", matching the cell's heading, in the ten Example sources, how-tos 06 and 26
  and project_templates' module docstring (the Template's own list already said connect).
  **Decided: `to_8_6` writes it too** (`upgrades._code_cells_line_as_8_6`), so an upgraded
  Example project still equals today's: where a Table notebook's text cell holds the list as
  8.2 to 8.5's Example projects wrote it, it becomes 8.6's, in a fixed three-line form the
  sources now use; a list of your own is left. CHANGES.md's "To update from 8.5" says so.
- **Copilot file 18**'s `run_values=` bullet, the second read's stop: a write the build adds is
  its table's `write()`, taking no arguments, and `run_values=` gives a Run value inside it the
  user's value.
- **The beginner reader again**, on just these texts
  ([report](../reports/beginner-reader-cleanup.md)), 20 stops. Mended: the failing doctest's
  line (19); the `RUNS` bullet (7); `INSERT_INTO` introduced by its printed Hive, and a table
  with no Partitions (6, 8, the how-to saying a passed-over SELECT's rows aren't in
  `results`); warehouse.py's "which one" and what to change (1 to 4); the Template's Run
  value and Build comments (10, 11); weekly_team's own Build and Run comments (12, 13), gone
  with those cells, as above;
  build_run's comments and wrap (16 to 18); "your query" matching the heading (9); file 18's
  bullet (20). Answered: 5, the README's `leave_out=` and `run_values=` lines, clear on a
  second read and left as the build_run docstring words them; 14, above; 15, VS Code's
  command, left as named.
- **The README's 8.6 Update bullet**, after ticket 12's review (87f70cef, merged in): only
  the Toolbox's notebooks are connected; a notebook of your own that imports from warehouse,
  and one of the Toolbox's whose import can't be connected, are marked to connect by hand; and
  where `conn` was the Example database, a line importing `conn` or reading `warehouse.conn`
  is marked, as CHANGES.md's "To update from 8.5" says.
- Tests: the whole suite passes on the merge with dev at 87f70cef (exit 0), its snapshot
  written again.
