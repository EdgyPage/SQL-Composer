# project.build_run

Type: task
Status: resolved
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

Built 2026-11-09.

- `built = project.build_run(statements, *, run_values=None, leave_out=None)`, last in
  `__all__` and `PROJECT_NAMES`, its work in `scheduled_runs.build_run`. **Decided: it takes the
  `statements` function, not what it gives.** It reads and checks the parameters (03) first and
  gives the values read back to the notebook's names, then calls `statements()` within the Run
  values `run_values=` gives, so the Statements are built with both; ticket 05's
  Guards-as-Warnings mode wraps the same call. Anything but a function taking nothing is
  refused.
- It runs in a Scheduled run's notebook: the calling notebook's folder, or the folder you work
  in, must be `scheduled_runs/<name>/` holding `<name>.ipynb`, which it reads the parameters
  cell of; elsewhere it is refused.
- `statements()` gives a dict of Statements by name, or a list; each value may be one Statement
  or a list, as a `write()` gives. Each is a SELECT, a write, an Admin statement, an Unchecked
  statement or a Python step; anything else is refused, naming it, Session settings among them.
  **Decided: a write is what `run_tables` writes with**, so `create_table(...)`'s and an upkeep
  Statement pass too. A SELECT is named by its key in a dict; in a list by the logic function it
  came from. **Decided: `load` marks each Statement a logic function gives with the function's
  name only while the build calls `statements()`** (`project.logic_functions_marked`,
  `LOGIC_FUNCTION`): elsewhere `load` gives each function as it is, since a wrapped function's
  `__globals__` are no longer the logic cell's, which a test of the Example projects reads; a
  profile hook would have done it too, but `code_audit` refuses `sys.setprofile`. Refused: two SELECTs under one key, two from one function in a list,
  and a SELECT of the run's own in a list, which has no name.
- The writes of each Project table (a Table folder the registry lists) that any Statement reads
  are added, all the way up, each through `load` and `writes_of`, as `run_tables` adds them;
  none the run writes itself; a table outside the Project is only read. `leave_out=` leaves a
  table out, and what only it reads; a name it wouldn't add is refused, naming those it would.
- All go through `lineage.in_order`, a loop refused naming its tables and saying to leave one
  out with `leave_out=[...]` (`in_order` gained `leave_one_out_with`; `tables_read` and
  `tables_written` lost their `_`, as `scheduled_runs` reads them). Each Project table's
  `session_settings()` is kept, and printed before its first write, as `run_tables`' dry run
  prints it.
- `run_values={"period_end": END}`: while the build runs, each Run value whose function is named
  `period_end` gives that value, its function not called (`run_values.values_given`, in
  `_traced_call`, so `run_value`, a Script tag's function and `tag_text` all reach it), a
  `write()` that takes nothing included. **Decided: a value that is a parameter, as the notebook
  held it, is used as read**, since `run_values={...}` is written before the build reads
  `END`. A name no Statement's Run value has is refused, naming those it has; the build prints
  each it gave.
- `START_FROM` passes over each Statement before that table's first write, and the build lists
  them; a table no Statement writes is refused, naming those it writes.
- It prints the parameters, the Run values given, what `START_FROM` passed over, then each
  heading, `-- 3 of 7: mart.team_days (read by week_totals)`, and its Hive, and a last line;
  it sends nothing. **The built run** (`scheduled_runs.BuiltRun`): `parameters` (each
  `Parameter`: name, hint, value given, value read), `steps` (each `RunStep`: `statement`,
  `name`, `result`, the name its rows come back by for a SELECT, `table` and `read_by`), in the
  order sent, `passed_over`, `settings` by table, and `given`, the Run values run_values= gave.
  Ticket 06 adds `run(query, execute)` to it.
- Tests: `tests/test_build_run.py`: a SELECT-only run, two levels up pulled, a table the run
  writes not added again, `leave_out` and its refusal, a loop, an override reaching a `write()`,
  a parameter given in `run_values`, an unknown Run value, the names in a list and their
  refusals, what no run sends, an Admin and an Unchecked statement, `START_FROM` and its
  refusal; and `build_run`'s docstring example.
- Left for ticket 05: the Guards-as-Warnings mode around the `statements()` call; 06:
  `built.run`, sending `dynamic_partitions` once first where a write needs it, as `run_tables`
  does, and each table's settings as the build printed them; the docs (ticket 10): the README,
  CHANGES.md, Copilot file 18.

### The code review (2026-11-09)

The review of tickets 02 to 04, mended in `fix(8.6): tickets 02 to 04's code review`:

- **Decided, in place of "a value that is a parameter is used as read": a `run_values=` value
  is read by the hint of what the overridden Run value's function gives back**, with the
  readers the parameters use (`scheduled_runs._run_value_read`, through a `read` that
  `run_values.values_given` now takes). The swap by identity (`value is parameter.given`)
  could take a literal `"7"` for another parameter's value, as CPython keeps one `"7"`; now
  nothing is matched against the parameters. A function with no hint, or one the build doesn't
  read, takes the value as it is; one that can't be read is refused, naming the Run value and
  its hint. The build prints each as used, with `read from "7"` where reading changed it.
  Tests: the collision, a refusal, and a function with no hint.
- Renamed: `scheduled_runs.build_run` to `build_scheduled_run`; `Parameter.given` to
  `Parameter.passed_in`; `BuiltRun.given` to `BuiltRun.run_values`, now each value as read;
  `_shown` to `_path_in_project`; `met` to `run_values_met`; `_added_writes`' `writes` to
  `writes_of_table` and `would_add` to `every_table_read_up`.
- `_read_value`'s empty test is `_is_left_empty`, an `if`; `_refuse_unread`'s and
  `_split_at_start_from`'s fixes are built with an `if`.
- One thing or a list of them, as a list, is `shared.items_of` (a new row in the standard's
  "One way per job"), in `_given_steps`, `_named_steps`, `_list_items` and project.py's
  `_marking_what_it_gives`; `_list_items` now reads a single value given for a `list[...]` as
  a list of it, as the text `"5"` already was.
- `TYPES_READ` is the one map of the types read: each a `TypeRead`, its reader and how it is
  passed, in place of `PASSED_AS` and `_read_one`'s dict.
