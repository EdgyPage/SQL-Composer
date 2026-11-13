# The schedule Workflow

Type: task
Status: resolved
Blocked by: -
Size: M

## Question

Adding a Scheduled run is a cell of `admin/scheduled_runs.ipynb` (Q9, Q18). The user's words: "I
want whatever happens in project.new_scheduled_run() to happen. Just moving the existing
functionality in to its own workflow."

## Done when

- **A Workflow notebook,** `admin/workflows/schedule/schedule.ipynb`, written by `workflows.py`
  like the others, reads top to bottom: a names cell with `NAME = "..."`, then the cell that
  does what `project.new_scheduled_run(NAME)` does.
- **It adds nothing** `new_scheduled_run` doesn't do: no proposals, and no cells of the run
  filled.
- `admin/scheduled_runs.ipynb` loses `NEW_RUNS`. `RUNS` and `TABLES` stay.
- **Removing a run** is in `admin/remove.ipynb`, beside the other removals, if it isn't there
  already.
- `project.new_scheduled_run` stays, for code.
- The Workflow runner runs its steps, `tools/workflow_graph.py` reads them, and the README's
  "The Workflows" section gets its chart and steps, as every Workflow has.
- The Example project's `weekly_team` notes how it was made.
- Ticket 14's Upgrade makes the folder and takes `NEW_RUNS` out.

## Answer

Built 2026-11-13.

- **`workflows.SCHEDULE`**, the seventh Workflow, last in `WORKFLOWS`. Its notebook,
  `admin/workflows/schedule/schedule.ipynb`, which `project.start()` writes as it writes the
  others: the cell finding the Project, the names cell `NAME = ''  # the Scheduled run's name,
  ...`, step 1, "Make the Scheduled run's notebook", whose cell is
  `project.new_scheduled_run(NAME)`, then `project.do_next()` and the run cell,
  `project.run_workflow("schedule")`. One file step, done once
  `scheduled_runs/<name>/<name>.ipynb` is there (`every_run_made`), run by `make_the_runs`,
  which calls `new_scheduled_run` and nothing else: no decisions cell, no proposal, no cell of
  the run filled in. `check()` names the step once `NAME` is filled in and saved, `do_next()`
  and `run_workflow("schedule")` run it, and a second run says every step is done.
- **Decided: `NAME` takes one name or a list, as `new_scheduled_run` does** (and `NEW_RUNS`
  did). The runner makes each name its own instance, as convert's `NAME` list does. One name is
  passed as text, so the Admin log records `project.new_scheduled_run("weekly")`, as before.
- **Decided: `is_finished` and `is_compared_again` take the Workflow.** Only convert's batches
  finish; without it, a Scheduled run named as a finished batch
  (`admin/workflows/convert/finished/<name>/`) was taken for done, and `check()` never named its
  step. Three call sites in `project.py` follow.
- `admin/scheduled_runs.ipynb` loses its `NEW_RUNS` cell; its text points to the schedule
  Workflow. `RUNS`, `TABLES`, `check()` and `export_project_lineage()` stay. `remove.ipynb`
  already archives a run (`SCHEDULED_RUNS`, since 8.6), now held by a test.
  `project.new_scheduled_run` is unchanged.
- **Docs.** `tools/workflow_graph.py` draws it: `docs/workflows.md` (its heading says the schedule
  Workflow makes a run's notebook), the README's new `### schedule` chart and steps, how-to 29.
  Also the README's Workflow rules, "Scheduled runs" step 1, its by-hand list and "Every file of
  a Project"; how-tos 01, 28 (the 8.0 step's checklist now lists the notebook it adds) and 31;
  Copilot file 18 lists the step under "Background, not a step of yours"
  (`{workflow: schedule}`, 7,6xx characters), and `test_one_source_of_steps` maps schedule to
  file 18.
- **Decided: a notebook term, "Scheduled run"**, in `NOTEBOOK_TERMS`, and the step's name and
  the about text name `admin/templates/scheduled_run.py`, not "Template", whose term says
  "Table notebook" (beginner reader, stop 1).
- **Example project.** `tools/example_project.py` makes `weekly_team` as a user does:
  `NAME = 'weekly_team'` typed into the intermediate's schedule notebook, then
  `project.run_workflow("schedule")`. Its README's row says so. Its Admin log entry is unchanged.
- **Decided: the Scheduled run's journey makes the run through the schedule notebook**: the
  cells before step 1, then the run cell. That is three actions where 8.6 counted one call in a
  cell of the user's own, so `KNOWN_ACTIONS` goes from 10 to 12, and `KNOWN_FIDDLING` gains
  `"schedule": ()`. **For the user:** this raises a count the journeys say only falls; 8.6's
  count left out the cells around the call.
- **For ticket 14.** `tests/test_upgrades.py`'s `AWAITING_ITS_STEP` leaves out
  `admin/workflows/schedule/schedule.ipynb`, which the intermediate fills in; 14 moves it to
  `GAINED_BY_HAND["8.7"]["intermediate"]`. Today the 8.0, 8.1, 8.2 and 8.6 steps add the schedule
  notebook through `add_what_start_makes`, and 8.6's writes `scheduled_runs.ipynb` as
  `ADMIN_NOTEBOOKS` holds it now, without `NEW_RUNS`; a Project already at 8.6 gets neither
  until 14's step.
- Tests: `tests/test_schedule_workflow.py` (7); `test_run_lineage_and_describe_logic`'s
  `NEW_RUNS` test is gone; the Workflow-wide tests count seven Workflows. The whole suite passes,
  the snapshot written.

### The beginner reader

[Report](../reports/beginner-reader-ticket-08.md). Fixed: stop 1 (Terms), 4 (the step says
running it again is refused once done), 5, 6, 8 and 9 (wording), 10 (Copilot file 18's section
headed as background). Left for the user:

- Stop 2: the run cell's "dry_run=True to see the Hive it would send" and the setup cell's
  `connect(...)` are written for every Workflow, upgrade's too; this one sends nothing.
- Stop 3: three ways to run one step (its cell, `do_next()`, `run_workflow`), as every Workflow
  without decisions has.
- Stop 7: the README's Workflow definition speaks of Decisions, which schedule has none of.

## Code review

Fixed point 89798750; `review-standards` and `review-spec` on Sonnet.

Standards (no hard breach):

- `make_the_runs`'s conditional expression: **fixed**, a plain `if`, with why one name is
  passed as text.
- `every_run_made` not named `is_`/`has_`: **answered**, it matches the file's done checks
  (`every_table_written`, `every_reference_written`).
- `tools/example_project.py`'s redundant `startswith` guard: **fixed**.
- `is_finished` gaining `workflow` (Shotgun Surgery, a switch on `CONVERT`): **answered**,
  whether a batch is finished is convert's question alone, and each caller holds the Workflow;
  testing it in each caller would repeat the switch three times.
- Test helpers like others' (`code_cells`, `started`, `files_of`): **answered**, each test file
  keeps its own, as `test_new_scheduled_run.py` does; `name_typed` renamed `type_name`.
- The README's step 2 line past the wrap: **fixed**.

Spec (no gap):

- Ticket 14 must take `NEW_RUNS` out of Projects it upgrades: **answered**, this ticket's last
  line and 14's step; noted above.
- Scope: the `is_finished` fix, the "Scheduled run" term and Copilot file 18's section:
  **answered**, the first keeps `check()` naming the step, the others are the docs "as every
  Workflow has" and the beginner reader's fixes.
- `NAME = ''` left empty: **answered**, `starts=True` leaves the Workflow not started, so no
  step runs.
