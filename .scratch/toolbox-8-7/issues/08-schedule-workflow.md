# The schedule Workflow

Type: task
Status: open
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
