# What stops blocking: CONVERSION marks, TODO lines, steps that only print

Type: task
Status: open
Blocked by: 02
Size: S

## Question

Three things block a Workflow today that need not (map, "What stops blocking": Q5, Q12,
Q13).

## Done when

- A `# CONVERSION:` mark blocks nothing: it stays in the logic, listed in `batch.md` and the
  checklist view; the compare step is the check.
- A `TODO:` line blocks nothing: check() lists it. `every_reference_filled_in` waits only on
  placeholders and the Decisions of its step's kinds.
- A step that only prints, new_table's preview and change_a_saved_table's `show_hive`, blocks
  nothing: `do_next()` and the runner print it and go on; check() lists it as read this. The
  check change_a_saved_table's Check first line names stays a step.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): no journey deletes a
  CONVERSION mark or a TODO line to go on.
