# project.build_run

Type: task
Status: open
Blocked by: 03
Size: L

## Question

Building is apart from running (Q3): the Statements a run names, with the writes of what they
read, in lineage order, Run values worked out now, the Hive printed, nothing sent (Q7, Q8, Q14,
Q16).

## Done when

- `project.build_run(statements, *, run_values=None, leave_out=None)` gives a built run:
  - each Statement given: a write, a SELECT, an Unchecked statement, an Admin statement or a
    Python step; anything else refused, naming it;
  - each Project table any of them reads, all the way up, has its Table notebook's writes
    added (through `load`, as `run_tables` does), less `leave_out`; a `leave_out` name that
    isn't one of those is refused, naming what it could be; a table outside the Project is
    read only;
  - all in lineage order (`in_order`), a loop refused naming its tables; Session settings
    sent as `run_tables` sends them;
  - `run_values={"name": value}` overrides each Run value of that function's name for this
    build, a `write()` that takes nothing included; a name no Statement's Run value has is
    refused, naming those it has; the build names each it overrode;
  - it prints the parameters (03), then the order, each headed like
    `-- 3 of 7: mart.team_days (read by week_totals)`, and each one's Hive; it sends nothing.
- A SELECT is named in `results` by the name it is given in `statements()`: a dict
  (`{"week_totals": ...}`) names them; a list is named by the logic function each came from.
- `START_FROM` (03) skips each one before that table's first write, and the build says so.
- Tests: upstream pulled, `leave_out`, two levels deep, a loop, an override reaching a
  `write()`, a SELECT-only run.

## Answer
