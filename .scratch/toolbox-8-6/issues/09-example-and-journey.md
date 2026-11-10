# A Scheduled run in the Example project, and its journey

Type: task
Status: resolved
Blocked by: 06, 07, 08
Size: M

## Question

The intermediate Example project shows a Scheduled run working, and a journey counts the
user's actions.

## Done when

- `tools/example_project.py` makes `scheduled_runs/weekly_team/` in the intermediate Project:
  a `WEEK: datetime.date | None` parameter, a Run value of its own for the week's first day,
  `load("mart.team_days").week_totals(...)` as its SELECT, and `mart.team_days`' upstream
  pulled in. Its built Hive and lineage committed, made by hand as the map says.
- A journey in `tests/journeys/`: make the run, fill its cells, run it through as a scheduler
  would (every cell, a parameter given as text), then once with a failure and its START_FROM.
  Its actions in `KNOWN_ACTIONS`.
- The starter Project gets the empty `scheduled_runs/` only.

## Answer

Built 2026-11-09.

- `tools/example_project.py` gains `SCHEDULED_RUNS` (`"intermediate": ["weekly_team"]`, the
  starter none, so it keeps the empty `scheduled_runs/` `start()` makes, which git doesn't
  hold) and two steps: `_add_scheduled_runs`, after the Conversions, runs
  `project.new_scheduled_run("weekly_team")` and fills in its cells; `_export_scheduled_runs`,
  after each table's Hive, connects `warehouse.py` to the Example database, as
  `admin/scheduled_runs.ipynb`'s cell under the Project's path does, and calls
  `project.export_run_hive(["weekly_team"])` and `project.export_run_lineage(["weekly_team"])`:
  `scheduled_runs/weekly_team/weekly_team.hql` and its `lineage/` pair, committed.
- **Decided: the source holds only the cells a user fills in**,
  `tools/example_project_sources/intermediate/scheduled_runs/weekly_team.py`: `# parameters`
  and `# scheduled`, in `# %%` cells. Each is written over the notebook's code cell of the same
  first line (`scheduled_run_cells`, `cell_starting`, refusing with `TodoMissing` when the
  Template's cells change); the text cell, the setup cell (its `connect(...)` filled in as every
  Example notebook's is), the Build cell (`run_values={}`, `leave_out=[]`) and the Run cell stay
  as the Template wrote them.
- The run: `WEEK: datetime.date | None = None`; `statements()` gives
  `{"week_totals": project.load("mart.team_days").week_totals(run_value(week_first_day),
  run_value(week_last_day))}`, and the build adds `mart.job_day_costs`, `mart.job_day_facts`
  and `mart.team_days`' writes before it: 4 Statements. **Decided: two Run values of the run's
  own, `week_first_day` and `week_last_day`**, since `week_totals` takes `(first_day,
  last_day)`, not `(week_start, day)`: the Monday of WEEK's week, and the Sunday after it.
  **Decided: when WEEK is None, the latest Partition is `ops.job_events`'**, through
  `latest_partition(job_events.dt, query)`, not `mart.team_days`': the Example database holds
  no mart table, and as the run builds, before it writes, `mart.team_days`' latest day is the
  last run's; `ops.job_events` holds the day the tables it writes end on.
- **Decided: `admin/scheduled_runs.ipynb`'s `RUNS` stays `[]`** in the Example project, as
  `remove.ipynb`'s lists do: a list typed for one use.
- The intermediate README tells of the run and its file table gains three rows (the
  notebook, `weekly_team.hql`, its `lineage/`); both READMEs' admin row names
  `scheduled_runs` (D482, fixed). CHANGES.md's 8.6 has a bullet. `tests/test_upgrades.py`'s
  `GAINED_BY_HAND["8.6"]` names the starter's README, and the intermediate's README,
  `admin/registry.csv` and `scheduled_runs/weekly_team/`, for ticket 12's comparison (today
  xfailed until its step).
- The journey, `test_a_scheduled_run_made_filled_in_run_by_a_scheduler_and_rerun_from_a_failure`
  in `tests/journeys/test_workflow_journeys.py`, in a copy of the committed intermediate
  Project, its run moved out with `project.remove_scheduled_run`, the three mart tables
  created in the stand-in warehouse as their notebooks' step 1 did: the run made, its
  `connect(...)` and its two cells typed from the same source (the notebook then equals the
  committed one, but its connection), its cells run down to the Build cell to read the Hive
  (nothing sent); then a scheduler's run (`ScheduledRunJourney.run_as_a_scheduler`: every
  code cell through `notebook_runner.run_cell`, a fresh namespace and the Project's modules
  forgotten, a `# Parameters` cell after the tagged one, `WEEK = "2026-09-23"` as text), whose
  `results["week_totals"]` is checked against `mart.team_days`' rows; then one whose
  warehouse fails `mart.team_days`' write (`FailingOneWrite`): it raises, prints
  `START_FROM = "mart.team_days"`; then the rerun with it, which sends neither job_day write.
  **Decided: the stand-in is taught Hive's NEXT_DAY for the journey** (sqlglot's executor's
  `ENV["NEXTDAY"]`, monkeypatched), as `week_start` writes it and the Example database's
  executor has none; the Toolbox is unchanged.
- **Its 10 actions, in `KNOWN_ACTIONS`**: running `project.new_scheduled_run(...)`, typing the
  setup cell's `connect(...)`, the `# parameters` and `# scheduled` cells, running the 4 cells
  down to the Build cell, scheduling it, and scheduling it again with START_FROM. **Decided:
  the connect line is an action here**, unlike in the Workflow journeys, where every notebook
  is connected once as the Project starts: a run is a notebook made later. The scheduler's own
  runs are not the user's.
- What the run showed of tickets 02 to 08, left for ticket 10 or later: no notebook has a
  cell that makes a Scheduled run, so the user types `project.new_scheduled_run(...)` in a cell
  of their own (`admin/scheduled_runs.ipynb` could take a `NEW_RUNS = []`); `run_values=`
  can't move both days of a week at once, as `week_last_day` calls `week_first_day` itself, so
  `WEEK` is the way in; `weekly_team.hql` shows the "dynamic_partitions" SET before each write,
  as `show_hive` does, where `built.run` sends it once first; and the build adds each table's
  write, not its `create()`, so on a warehouse that lacks a table the run fails at its first
  write (the Table notebook's step 1 creates it).
