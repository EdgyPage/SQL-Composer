# The Example project's change

Type: task
Status: resolved
Blocked by: 06, 07
Size: M

## Question

The intermediate Example project shows a real Inherited change, read on main as the Example
projects page (Q18).

## Done when

- **`tools/example_project.py`**, building the intermediate Example project:
  1. records its first state;
  2. makes one real change: the Building block `events_per_job` counts a retry as a run too,
     so `mart.job_day_facts.runs` has an Own change from that block and
     `mart.team_days.runs`, which reads it, an Inherited change (2026-11-17: nothing in the
     intermediate project reads `mart.team_failures`, the map's first choice, so its change
     would show no Inherited change);
  3. runs `mart.job_day_facts`' cell 5, which records again;
  4. writes one table's next write, so the difference shows "first written with this logic";
  5. exports the difference from `admin/lineage.ipynb`.
- The change stays in the example, its Table notebook saying why in a line.
- `lineage_state.csv` and the difference page are committed, regenerated whole on CI, and the
  Example projects page shows the difference page.
- **A journey** in `tests/journeys/` does the same in a copy, counting its actions.
- The starter Example project holds `admin/lineage.ipynb` and its first recording only.

## Answer

Built 2026-11-17, from dev's 16ac7719 (tickets 01 to 07).

- **`tools/example_project.py`'s `_change_later`**, the last step before `_tidy`, for each
  project `LATER_CHANGES` names (the intermediate one: `events_per_job` and
  `mart.job_day_facts`), on `CHANGED_TIME`, the day after `PINNED_TIME`:
  1. copies the Building block's changed source,
     `tools/example_project_sources/intermediate/changed/building_blocks/events_per_job.py`:
     `runs` counts `is_in(job_events.event_type, ["start", "restart"])`, where it counted
     `equals(..., "start")`, and its docstring says why in three lines (a restart, the event
     the scheduler sends from 2026-09-26 on when someone starts a job again by hand; changed the
     day after, so the difference shows it). The why is in the block, not the Table notebook,
     since the block is what changed.
     **A change to the ticket:** a restart, not a retry. Counting the Example database's
     retries changed `runs` on 2026-09-14, so the Example project tests' worked numbers and
     usability scenario W8's answer key would have had to change with it. The Example database
     holds no restart yet, so the logic changes and no row of the data does;
  2. runs `mart.job_day_facts`' cell 5, `export_hive()`, from its Table folder, which records
     (`recorded_by` `tables/mart__job_day_facts/mart__job_day_facts.ipynb export_hive()`) and
     writes its `.hql` again;
  3. on `WRITTEN_TIME`, an hour later, writes the table once, `run_execute(write(), execute)`,
     connected to the Example database, which adds its row to `admin/sent.csv`;
  4. runs `admin/lineage.ipynb`'s cells by hand, as `_export_scheduled_runs` runs
     `scheduled_runs.ipynb`'s: `record_lineage_state()` ("no change") and
     `export_lineage_difference(since=None, tables=None)`.
- **What the difference shows**, `admin/lineage/20260926-070000-difference.html` and `.md`:
  "3 tables changed, since the recording of 2026-09-25 06:00:09, to the newest, of
  2026-09-26 06:00:00: 3 columns (1 own, 2 inherited)." `mart.job_day_facts.runs`, own change,
  "It came with a change to the Building block `events_per_job`", its logic before and after
  (`= 'start'` to `IN ('start', 'restart')`), first written with this logic 2026-09-26 07:00:00;
  `mart.team_days.runs`, inherited, `mart.team_days.runs` ← `mart.job_day_facts.runs`; and the
  Scheduled run's `weekly_team.week_totals.runs`, inherited through `mart.team_days.runs`. The
  Example projects page shows the page, since `toolbox_registry.lineage_pages` globs
  `*/**/lineage/*.html`.
- **The counts line** of a difference reads "1 own, 2 inherited", as a recording's report
  counts them (`lineage_difference.COUNT_WORDS`), where it read "1 own change, 2 inherited
  change".
- **The tests that change `events_per_job`** in a copy of the intermediate project (tickets 02,
  04, 05 and 07's) take its restart back out, `is_in(..., ["start"])`, since the committed
  block holds the change now; the two that read the difference page take the newest, since the
  copy holds the committed one too.
- **A journey**, `test_a_building_block_changed_then_found_in_the_lineage_difference` in
  `tests/journeys/test_workflow_journeys.py`, on the intermediate project as it was the day
  before (`the_day_before`: the block as first written, the state's rows before
  `CHANGED_TIME`, no difference, an empty `sent.csv`, the notebooks connected to the stand-in
  warehouse): the block saved, the Table notebook's cells 1 and 5 run, `run_tables.ipynb`'s last
  cell typed with `tables=` and `execute=` and its cells 1, 2 and that one run, then
  `lineage.ipynb`'s three cells; it reads the difference, and holds that the state's rows from
  `CHANGED_TIME` on match the committed Example project's. 10 actions, in `KNOWN_ACTIONS`.
- **The starter project** holds `admin/lineage.ipynb` and the recordings its Project actions
  made (ticket 03), not one recording alone: since 03, every action that makes a table records.
- **`tests/test_upgrades.py`:** `GAINED_BY_HAND["8.8"]` leaves the later change's files out of
  the straight-to-this-version comparison (the block, the table's `.hql`, `sent.csv`; its
  Lineage state and difference are lineage pages, left out already), which counts once the
  version is 8.8 (ticket 10); and the 8.1 hive-cell test makes the change in its copy, as the
  user made it, before it compares the `.hql`.
- **Left for the docs (ticket 09):** how-tos 19 and 31 copy the intermediate project and print
  its Hive, so each shows the changed `runs` line: 31's printed build, and 19's diff of the
  block, whose "after" text, written whole, now differs in `runs` too. Their expected output
  needs writing again, and 19's "after" text should keep the restart, so its diff stays about
  `minutes`.

## Comments

**Moved, 2026-11-17, after merging:** the later change is made an hour after the Project, at
2026-09-25 07:00, its write at 08:00, not the next day: every how-to is pinned to 2026-09-25
09:00 and copies the intermediate project as it ends, so a history running past that time put
how-to 32's own recording before the Example's write. The difference is now
`admin/lineage/20260925-080000-difference.html` and `.md`.
