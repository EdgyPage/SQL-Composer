# Templates and Example projects as Projects

Type: task
Status: resolved
Blocked by: 07, 08
Size: L

## Question

Map Notes, "Templates", "Example projects". The Table-notebook Templates in `# %%` form, the
Saved-table reference and Building block Templates; `notebook_start` and
`keep_table_references_true` folded into how-tos. Both Example projects rebuilt as Projects,
generated with pinned times, tested through `load` and `run_tables`.

## Done when

- The export ships both Example projects as Projects, and their tests pass.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built in two parts, each reviewed on its own: 09a, the Templates (2026-10-21, branch
`toolbox-6/09a-templates-in-the-toolbox`), then 09b, the Example projects as Projects.

### 09a: the Templates in the Toolbox

- `sqlglot_composer/project_templates.py` holds the five Table notebook Templates
  (`daily_table`, `incremental_load`, `weekly_rollup`, `as_of_lookup`, `quality_checks`), all
  built by `_notebook` around the same five code cells, each listing its placeholders with an
  example in its text cell; and the `saved_table_reference` and `building_block` Templates.
  `start()` writes all seven into `admin/templates/`; `new_table`'s `template=` takes only a
  Table notebook Template (one in `# %%` cells).
- `incremental_load`'s `write_day(day)` gives the writes of its last days, a list;
  `run_tables` sends each in turn, and its lineage cell passes them all.
- `export_lineage` from a Table notebook, of Statements of several tables of which one writes
  that notebook's table, goes in that Table folder's `lineage/` too: lineage across tables, as
  the prototype's team_day showed.
- The repo's `templates/` folder is gone, with the export's copy of it, the README's generated
  list (the README now names each Template), `test_templates.py` and the Level tests of
  Templates; `notebook_start` and `keep_table_references_true` become how-to steps (ticket
  10). `tests/test_project_templates.py` makes each Template into a notebook, fills it in for
  the Example database, loads it and runs its preview.

#### 09a's reviews

- Spec (2026-10-21): the fold of `notebook_start` and `keep_table_references_true` into
  how-tos had no owner (now in ticket 10's Question); CHANGES.md now says what became of each
  5.x Template; a test ties the README's list to the Toolbox's. Answered, against the
  prototype's stubs: `weekly_rollup` saves days and `week_totals` reads weeks, since a write
  fills the one day its FROM table is bounded to, so no Saved table of weeks can be written;
  `quality_checks` saves each day's row count, since `run_tables` writes every table through
  its `write_day`; `incremental_load` rewrites its last days, as 5.x's did, and its
  `write_day` gives a list, which `run_tables` sends in turn; a read table's file is
  `<SOURCE_NAME>` (or `<CHECKED_NAME>`, `<SNAPSHOT_NAME>`) in the Toolbox's Templates, as
  `<NAME>` is the table's own.
- Standards (2026-10-21): widths (each Template text starts on its own line); CONTEXT.md's
  Template entry no longer speaks of two sets; "writes it as the partition" now names the
  Date partition; `null_counts` names its counts with a `column_name` helper; lineage's
  `stems` split into `written` and `chosen`. Answered: `week_totals` reads `dt`, the day the
  Saved table reference Template names, and says so; `_notebook` stays a function of strings.
- Beginner reader (2026-10-21): each notebook's text cell now says to fill in its Table
  reference first, and which columns, types and Key it lists; `as_of_lookup` says the
  snapshot's reference needs its Key; `<TOTAL>` and `<TOTAL_NAME>` are told apart; why the
  snapshot's day is in ON=; why the day is grouped on but not selected, in every Template;
  `quality_checks` says how a small day shows; the example day is the same everywhere; the
  Building block shows how a notebook reads it; `<NAME>` is named; the logic cell's second
  line numbers it 2.

### 09b: the Example projects as Projects

Built 2026-10-21 on branch `toolbox-6/09b-example-projects-as-projects`.

- `tools/example_project.py` now makes each whole project as a user does, in a Python of its
  own started in an empty folder: `project.start()`, `project.add_references(...)` on the
  Example database with FILLED_IN filling each TODO and adding Aliases (`minutes` and `failed`
  on ops.job_runs, `high` on ops.run_alerts, `ends_a_run` on ops.job_events),
  `project.new_table(...)` per Saved table, then the hand-written sources in
  `tools/example_project_sources/<project>/` (each notebook as `# %%` cells, the Saved tables'
  references, the Building blocks and the README), `refresh_reference_sheet()`, and each
  table's lineage from its Table folder. The time, the commit and the calling script (a
  notebook) are pinned, so it writes the same files everywhere.
- The starter project: mart.daily_job_runs, mart.alerts_per_job and mart.team_day (whose
  lineage draws all three through `load`). The intermediate one: mart.job_day_costs
  (incremental_load), mart.job_day_facts (as_of_lookup), mart.team_days (weekly_rollup) and
  mart.job_events_checks (quality_checks), each writing its last 3 days, the 3 named once in
  `building_blocks/days_rewritten.py`. 5.x's settings-driven checks and lineage review are
  not carried over: the how-tos keep teaching them.
- The export copies a notebook or a CSV file unstamped (they have no comment syntax), and its
  dry-run check runs each project's `project.run_tables(DAY)` from its `admin/` folder, the
  Toolbox at main's top. The README's Example projects section says how to open them.
- `tests/test_example_projects.py` holds each project to its generator, checks it has no TODO
  left and nothing unregistered, loads each notebook's logic, and checks each preview against
  pandas; `tests/repo/test_levels.py` holds a Project's Levels (references/ and send.py 0,
  building_blocks/ 1, each logic cell 2). ruff skips the Templates' copies and the notebook
  sources, and F401 in `change_a_saved_table.ipynb`, whose examples are commented out.

#### 09b's reviews

- Spec (2026-10-21): `refusals.py`'s day-format fix pointed at the deleted
  `statements/example_1_job_day_costs.py`, and now names mart.job_day_costs's Table notebook;
  CONTEXT.md's Level and Example project entries still spoke of `run_pipeline.py` and a
  settings.py, and now give a Project's Levels and call an Example project a Project; the
  intermediate README and `days_rewritten.py` said every table writes its last 3 days, and now
  say the counting tables do, and why the checks write only their day. Answered: 5.x's
  settings-driven checks and lineage review aren't carried over (the how-tos keep them, and
  ticket 10 moves the how-tos to Projects).
- Standards (2026-10-21): lines over 96 wide wrapped; `write_here` split into its steps
  (`_set_the_day`, `_add_references`, `_add_saved_tables`, `_export_lineage`, `_tidy`);
  `table.replace(".", "__")` is now `project.table_stem`. Answered: the tool imports the
  private `_template_cells` and `_write_notebook`, with a comment saying why: a user fills a
  notebook in by hand in Jupyter, so a public way to write one over would be for this tool
  alone; FILLED_IN, SAVED_TABLES and LINEAGE_ACROSS stay three tables of data, each read by
  one step; the Example projects hold no `sqlglot_composer` folder, and their READMEs say to
  copy it in; `import pathlib` and `import sys` are two lines, and `change_a_saved_table.ipynb`
  has a per-file F401 ignore, since ruff lints notebooks.
- Beginner reader (2026-10-21): the Reference sheet left out condition Aliases (`failed`,
  `high`, `ends_a_run`), and now lists an Alias that reads one column alone in that column's
  row, a condition shown as `failed (a condition)`; how the day reaches PARTITION(...) and
  what `by_day` leaves of a joined table's bound are said plainly; `admin/run_tables.ipynb`'s
  DAY is the Example database's last day; `write_day` says when it gives a list; the admin log
  names commit `nogit`, what a folder outside git gives, rather than `pinned`; the starter's
  logic cells number themselves 2 like the others; mart.team_day's lineage cell says what
  `project.load` gives. Answered: the README's step 8 is ticket 10's to replace; the Reference
  sheet isn't logged, and its `exported_at` says when it was written; `GROUP_BY("week", ...)`
  and `column_name` say why where they are; ops.job_events' `minutes` stays out of
  `does_not_add_up`, which is for averages, ratios and distinct counts (its comment says so),
  and is added only at the events `ends_a_run` picks.
