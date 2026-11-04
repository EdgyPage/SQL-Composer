# PARTITION in the convert notebook's names cell

Type: task
Status: open
Blocked by: 01
Size: S

## Question

Step 7 tells the user to compare another Partition by running `print(project.compare_batch(...))`
"in a new cell" (map, Q24).

## Done when

- The convert Workflow has an input, `PARTITION = None`, its comment saying what to write, such
  as `{"dt": "2026-09-23"}`. Step 7's cell passes it: `project.compare_batch(NAME, query=query,
  partition=PARTITION)`. None compares the latest Partition both tables hold, as today.
- Step 7's text says to set PARTITION and run the step again; "in a new cell" is gone from it.
  Each result is kept beside the ones before, as today.
- The runner, `project.run_workflow`, passes it too.
- The convert journey compares a second Partition through PARTITION; `KNOWN_FIDDLING` loses the
  cell made by hand, if it lists it.

## Answer
