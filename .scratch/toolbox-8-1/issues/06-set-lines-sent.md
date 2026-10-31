# The write step sends the SET lines

Type: task
Status: open
Blocked by: 01
Size: S

## Question

A converted table's checklist asks the user to send the original's SET lines before its
write, with a call it prints (map, "What stops blocking": Q6).

## Done when

- `run_tables` sends each table's Session settings, its `session_settings()`, through
  `execute`, before its write, and records it in `sent.csv`; a table with none sends nothing
  more.
- The checklist and the Decisions have no SET-lines box.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): the long-script journey's
  SET lines reach the Warehouse with no step of its own.
