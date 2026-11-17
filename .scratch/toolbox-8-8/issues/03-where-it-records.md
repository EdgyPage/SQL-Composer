# Where it records

Type: task
Status: open
Blocked by: 02
Size: M

## Question

"Every time I change a table or reference, a lineage file would have to be generated." The
Toolbox can't see a logic cell edited in Jupyter, only the calls it is given, so it records at
each call that changes a table or Table reference (Q5, Q14).

## Done when

- **Each Project action that changes a table or Table reference** records at its end, its
  `recorded_by` naming the call: making or removing a Table folder or Scheduled run, adding
  Table references, `convert`, `promote`, `refresh_reference_sheet`, and the
  `change_a_saved_table` Workflow's last step. A Project action that takes many names records
  once, after the last.
- **A Table notebook's `export_hive()`** (cell 5) records, `recorded_by` naming the notebook,
  and prints ticket 02's line; cell 5's comment in `project_templates.py` says so. Cell 4's
  `export_lineage` doesn't record (Q14).
- **Never a Scheduled run**: `build_run` and `built.run` record nothing; a test holds it.
- A recording that fails, such as a CSV left open in Excel, never fails the action it ends: the
  action's report says what wasn't recorded and the cell that records.
- The Example projects' notebooks are regenerated with cell 5's new comment.
