# Writing Decisions into the files, and the checklist view

Type: task
Status: open
Blocked by: 02
Size: M

## Question

A Decision answered in the decisions cell reaches the files by a file step, never by the
user editing a generated file (map, "Decisions": Q1, Q9, Q11).

## Done when

- A file step writes each answered Decision into the table's files: `key=`, `location=`, a
  guessed type, in its Table reference; keep or fold, from 10. It runs in each Workflow with
  Decisions, before the step that waits on them, and `do_next()` runs it.
- The cell wins over what the Toolbox wrote. A file the user changed by hand is kept, and the
  step reports it, with a fresh copy beside it as a Batch run again does (`fresh/`).
- `tables/<t>/conversion/checklist.md` is generated and read-only: each Decision of the table,
  made or open, written again each time the Decisions are read. Nothing ticks a box by hand; a
  box the user ticks is written over, and check() says so once.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): no journey opens a Table
  reference to fill in a Key, a location or a type, or ticks a box: those entries leave the
  known-fiddling list.
