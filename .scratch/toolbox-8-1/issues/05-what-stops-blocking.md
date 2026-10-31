# What stops blocking: CONVERSION marks, TODO lines, steps that only print

Type: task
Status: resolved
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

## Answer

Built 2026-10-31.

- **`# CONVERSION:` marks** block nothing since 02 (the done-checks read Decisions, not the
  checklist). check() now lists them as notes: "Noted by project.convert(...), which blocks
  nothing: each opt-out keeps what the original did, and the compare step checks the rows";
  the checklist view lists them under "Notes, which block nothing".
- **TODO lines** block nothing since 02. Settled while building: check() doesn't list them,
  since every Project's Table references hold `does_not_add_up` TODO lines and check() would
  name them always; `project.write_decisions` counts each table's left ("1 TODO line left
  ... which waits on nothing: fill in each when you like"), `decisions.todo_lines`.
- **A step that only reads**, `Step.reads_only`: new_table's preview. `next_step` passes it
  over, so `do_next()` and check() go on to the step after it, and check() names it beside
  that step: "Before it, read what step 4 prints, which waits on nothing: ...".
  change_a_saved_table's show_hive step stays a step, as the map said: it runs the check its
  Check first line names.
- Tests: `tests/test_workflow_steps.py`'s ticket 05 section; test_conversions' mark wording.

### After the review (2026-10-31)

- One TODO line reads "fill it in when you like"; a test shows next_step passing preview over.
- Left as built, and why: TODO lines aren't in check() (above); change_a_saved_table's
  show_hive step is one step with the check it names, which the map keeps a step; do_next()
  passes a reads-only step over by next_step, and check() names it, rather than printing it,
  since its call reads the warehouse, which do_next() never does. read_before looks one step
  back, as no Workflow has two reads-only steps in a row.
