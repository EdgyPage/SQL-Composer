# project.new_run_value

Type: task
Status: open
Blocked by: 02
Size: S

## Question

Every W7 run wrote `building_blocks/run_values.py` by hand and registered it from no cell (map,
"Fewer Decisions written out").

## Done when

- `project.new_run_value(name, *, latest_partition)`: `latest_partition="ops.job_runs.dt"`
  writes `def <name>() -> datetime.date` returning `latest_partition(<table>.<column>, query)`
  into `building_blocks/run_values.py`, with its imports (made if missing), and registers the
  file, as `new_block` does. Its report gives the import line to put at the top of the
  decisions cell.
- Refused: a name already in the file; a table with no Table reference (naming the references
  Workflow); a column not one of its partition columns.
- Another kind of function is the file to edit, which the docstring and how-to 09 say.
- The convert notebook's decisions cell comment names it; no cell of its own (8.4's ticket 14).
- The journey (01) uses it in place of writing the file, its action count falling.

## Answer
