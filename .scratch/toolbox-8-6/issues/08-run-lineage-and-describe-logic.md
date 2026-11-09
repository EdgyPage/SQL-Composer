# A run's lineage and Hive, and describe_logic

Type: task
Status: open
Blocked by: 06
Size: M

## Question

One run's lineage and Hive written by hand into its folder (Q17, Q23); a Table notebook's
logic described for Copilot (Q25).

## Done when

- `project.export_run_lineage(name)` builds the run as its notebook's defaults give it and
  writes its lineage into `scheduled_runs/<name>/lineage/`, named by the time and the run.
- `project.export_run_hive(name)` writes the built Hive, in order, headed as the build prints
  it, into `scheduled_runs/<name>/<name>.hql`, to read, never to edit.
- `project.describe_logic(names)` prints each named table's logic functions: the signature
  with its hints, and its docstring's first line; a name with no Table folder refused, naming
  close ones.
- Each in `admin/scheduled_runs.ipynb`.

## Answer
