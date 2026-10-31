# Promote ends referenced: the Reference sheet and the Database modules

Type: task
Status: open
Blocked by: 01
Size: S

## Question

A promoted table is referenced only once the user refreshes the Reference sheet by hand
(map, "Referenced and maintained": Q19).

## Done when

- promote's last step, a file step, refreshes the Reference sheet and the Database modules
  for the prod tables, and `do_next()` and the runner run it.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): the promote journeys end
  with each prod table in the Reference sheet.
