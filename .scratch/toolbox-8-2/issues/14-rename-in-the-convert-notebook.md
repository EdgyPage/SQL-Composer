# RENAME in the convert notebook's names cell

Type: task
Status: resolved
Blocked by: 04
Size: S

## Question

Found by round one (W1-1, W1-2, W1-3, H1-1): every converter named its copy as the original,
adding rename= to the convert cell's call by hand, since the names cell has no place for it and
nothing near it says a copy is named <table>_<its database>.

## Done when

- The convert Workflow's names cell has RENAME, saying the default name, and its step and
  run_workflow pass it to project.convert, held by a test.

## Answer

`workflows.CONVERT` has `Input("RENAME", {}, ...)`, its convert step passes `rename=RENAME`, and
`convert_the_batch` passes it on. `tests/test_run_workflow.py::
test_rename_in_the_names_cell_names_a_copy_in_dev` holds it. A Project's convert notebook from
8.1 has no RENAME line: ticket 07's Upgrade step writes the Workflow notebooks again, keeping
each name given, as 8.1's did. W1 and H1 now name their copies, mart_dev.team_fails and so on,
which their reference ends type into RENAME.
