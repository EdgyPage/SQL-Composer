# PARTITION in the convert notebook's names cell

Type: task
Status: resolved
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
Built 2026-11-04.

- **The input**: the convert Workflow's last names-cell input, `PARTITION = None`, its
  comment "another Partition for step 7 to compare, such as {"dt": "2026-09-23"}: None
  compares the latest Partition both tables hold".
- **Step 7**: its cell is `project.compare_batch(NAME, query=query, partition=PARTITION)`; its
  text says to set `PARTITION` in the names cell and run the step again, each result kept
  beside the ones before; "in a new cell" is gone.
- **The runner**: `compare_the_batch` passes `PARTITION` when it is a dict, None otherwise.
- **Journeys**: one compares a second Partition by setting `PARTITION` and running step 7
  again, two results passed in compare.md; one sets it before `project.run_workflow` and the
  runner compares that Partition. `KNOWN_FIDDLING` lists no cell for it, convert's being `()`.
- **Upgrade**: a Project's convert notebook gains `PARTITION` and step 7's new cell in 08's
  Upgrade step, as the map says.
- **Code review** (review-spec, with standards, on sonnet): every bullet met. Answered: once
  a batch is finished, the runner sees step 7 done and compares nothing more, so a PARTITION
  set later is compared by running step 7's own cell again, as its text says; set before the
  first run, the runner compares it, which a journey holds. In the same commit, D416: the
  block and the "still <FILL IN>" note named "step 3", which in new_table is step 5; they now
  name what the step does, writing the answers in, and `project.write_decisions(DECISIONS)`.
