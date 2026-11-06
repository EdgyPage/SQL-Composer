# A journey of the 8.5 path, counting your actions

Type: task
Status: resolved
Blocked by: none
Size: M

## Question

Speed is fewer of the user's actions (map, Q1). Before anything changes, a test should count
them, so each ticket after shrinks a number it can see.

## Notes

The journeys already list hand edits in `KNOWN_FIDDLING`, but do other hand work unlisted
(map, "What the user does by hand today"): set `conn`, fill DEV and PROD, save the .hql, write
`run_values.py`, type the decisions cell.

## Done when

- **Every action a journey takes for the user is counted**, by kind: a value typed into a names
  or decisions cell, a cell run, a file written or edited by hand, a call no shipped cell
  holds. `Journey` records each; `KNOWN_FIDDLING` stays the list of hand edits, and a new
  `KNOWN_ACTIONS` holds each Workflow journey's count, which only shrinks.
- **The user's batch through convert then promote** (8.4's PERIOD_SCRIPT, its Run value and
  seed limit) is the journey 8.5 is measured on, its count recorded here as the baseline.
- A test fails when a journey's count rises, naming the action that was added.

## Answer
Built 2026-11-05.

- `Journey.took(kind, what)` notes each action, in `Started.actions`: "typed" for each name a
  names or decisions cell is given (`type_names`, `type_decisions_cell`, `paste_decisions`),
  "ran" for each code cell run and the run_workflow cell, "file" for each file saved by hand
  (`Journey.save_by_hand`, which every journey's script and Run value file now go through),
  "by hand" for each `make_by_hand` edit.
- `KNOWN_ACTIONS`, by test name; the fixture's teardown (`_check_the_actions_taken`) fails a
  measured journey taking more, listing each action, and one taking fewer, asking for the number
  to be lowered.
- **Baseline, 8.4 at dfd5cc4d**: the user's batch converted and promoted through the notebooks
  (`test_promote_a_seeded_table_limiting_its_prod_seed`), **35**; converted through the runner
  (`test_convert_the_users_batch_with_run_values_through_the_runner`), **14**.
- Found: the runner journey passed only after another test, a module cached: its decisions cell
  imported the Run value before step 1 wrote `references/ops__job_runs.py`. It now runs to the
  Decisions first, then writes the file and answers, as a user must, and passes alone. That is
  the order 02's layout makes the path.
