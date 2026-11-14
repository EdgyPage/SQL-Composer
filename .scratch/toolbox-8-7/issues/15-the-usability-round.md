# The usability round

Type: task
Status: open
Blocked by: 01, 14, 16
Size: M

## Question

Can a user with no context still follow the Workflows from what main ships (Q22)?

## Done when

- `plan` runs on every scenario, and only those it says to run are given to agents (ticket
  01's memo).
- **W8 is redone** to start its Scheduled run through the schedule Workflow.
- **A new W9** converts a script with a Script tag, answers it with `hivevar(...)` and a default,
  then exports it for a scheduler, and checks the `.hivevars` file against its answer key.
- Every dev scenario the round runs passes three of three, held-out once, recorded in
  `.scratch/usability-loop/results.md` with each run's inputs.
- **The beginner reader** reads the Workflows overview page and a lineage page's side panel,
  and its report is linked here.
- Each finding is fixed in what a user reads, or recorded for the next version.
