# The runner: run_workflow, one or many, dry_run

Type: task
Status: resolved
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

## Answer

Built 2026-10-31.

- **The runner:** `project.run_workflow(workflow, *, query, execute, dry_run=False,
  change=None)` walks each instance's steps after the last its files say is done
  (`workflows.steps_left`, which `next_step` now shares), passing over each step done. A file
  step runs as `do_next()` runs it (`Step.run`); a step that calls the warehouse runs through
  its new `Step.send(inputs, calls)`, the same calls its cell makes (`workflows.Calls`, with
  the send functions beside the file steps' functions). After each step the instance is read
  again (`workflows.read_again`), since convert records the batch's tables as it runs.
- **Where it stops:** a decision step not done, named as check() names it (its open
  Decisions listed); a step with no call; a refusal or the warehouse's error, written whole
  under "Stopped:"; or a step that ran and isn't done, such as a compare that failed. Each
  stop says to mend it and run again. A stop in one instance stops the rest.
- **dry_run=True:** settled here: it sends nothing through execute, but runs the steps that
  change only files and those that only read through query (convert's and add_references'
  DESCRIBE), so one dry run reaches every create, seed and write and says each one's Hive
  ("would send: ..."; run_tables' own dry run, captured, for the writes, in its order with
  its SET lines). A compare or a preview says what it would read.
- **One or many:** a NAME list in convert's names cell is one instance per batch
  (`workflows.one_per_name`), each a batch convert made already: FILES and HIVE convert the
  batch NAME names alone. The runner runs only what the names cell names, never another
  batch convert made, since it sends. A finished batch is done (`workflows.is_finished`): check() and the
  runner pass it over, where before a names cell still naming it showed step 1 again.
- **change_a_saved_table:** settled here: its Admin statement lives only in its notebook, so
  the runner takes it, `change=change`, which that notebook's last cell passes
  (`Workflow.run_with`); without it, step 2 stops saying so. Step 2, the check of its Hive,
  stays the user's (the map's Q13): a step no file tells of that only prints stops a run once
  it has printed, so the runner shows the change's Hive, its Check first line with it, and
  stops; step 3's own cell sends the change. A step that only reads, new_table's preview,
  waits on nothing: the runner prints it and goes on.
- **Each notebook's last cell** (`workflows.run_cell`) calls it, after `project.do_next()`,
  which is unchanged; how-to 29 shows each one.
- **Found on the way:** `_every_decision_answered` said yes before any Table reference was
  written, so a decision step counted as done before the step that asks it; and
  `project_is_current` compared the whole of project_version.txt, its comment lines too,
  with the version, so the upgrade step never read as done. Both fixed.
- **Tests:** tests/test_run_workflow.py (a name no Workflow has, not started, a stop at an
  open Decision then going on, a step that ran and isn't done, a NAME list and which a stop
  names, a dry run sending nothing, change= missing, each notebook's last cell); and the
  journeys run each Workflow a second way, one run_workflow call after a dry run that must
  leave the warehouse's `executed` list as it was: convert then promote, references,
  new_table then change_a_saved_table, and upgrade.
- **Code review:** Standards: the `TablesOf` alias and the closures that needed it (now plain
  step functions over `_send_creates`, `_send_seeds` and `_send_writes`), a table list not
  through `in_words`, `change` hinted `object` (now `Statement | None`), `run_cell` named for
  what it returns (`run_cell_text`), `ran` and `again` (`step_lines`, `mend_line`), a
  conditional expression made an `if`, the slice insert made a new list, and the three
  `to_hive(...).split` made `hive_lines`. Left: the dry run's writes are run_tables' own dry
  run captured, so its order and SET lines stay in one place; the "convert, NAME" label and
  check()'s notebook label differ on purpose. Spec: the runner ran every unfinished batch
  (now only those the names cell names), the warehouse's `execute` lost its docstring
  (fixed), references' journey had no dry run (added). Left as settled: a dry run runs
  convert and add_references, which read through query and write files, since every later
  step's Hive needs their files; query and execute stay optional, since upgrade and
  references send nothing through execute, and a step that needs one is refused by its own
  call, naming it; a stop in promote, new_table or references names the Workflow, its one
  instance, and the step's own message names the table.
- **Beginner reader:** [07-beginner-reader.md](../reports/07-beginner-reader.md). It found the
  runner sent change_a_saved_table's change without stopping at the check of its Hive (now it
  stops there), the notebooks' opening still calling do_next() the last cell, and the dry run
  described as sending nothing when it converts for real; each stop, and what was done, is
  there.
