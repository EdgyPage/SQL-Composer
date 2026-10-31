# The runner: run_workflow, one or many, dry_run

Type: task
Status: open
Blocked by: 03, 05
Size: L

## Question

`do_next()` runs file steps only; every create, seed, write and compare is a cell the user
runs in turn (map, "The runner": Q7, Q16).

## Done when

- `project.run_workflow(workflow, *, query, execute, dry_run=False)` runs one Workflow's steps
  in order from its names and decisions cells, its calls to the Warehouse included. It stops at
  an open Decision or a failure, naming the instance, the step and what to do; run again, the
  done-checks skip what is done.
- `dry_run=True` sends nothing, and prints each step and the Hive each call would send.
- A names cell's NAME or TABLES may be a list: each instance in turn, and a stop names which.
- Each Workflow notebook's last cell runs it, beside `do_next()`, which is unchanged.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): each journey runs a
  second way, as one run_workflow call, to the same end goal, and a dry run of it sends nothing
  (the Example database's tables are unchanged).
