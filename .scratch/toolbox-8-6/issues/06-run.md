# built.run

Type: task
Status: resolved
Blocked by: 04
Size: M

## Question

Running, apart from building: writes through execute, reads through query, results by name, a
failure the scheduler sees (Q8, Q10, Q11, Q15).

## Done when

- `built.run(query, execute)` sends each in the build's order: a write, Admin or Unchecked
  statement through `run_execute`, a SELECT through `run_query`, printing a line as each
  works, as `run_tables` does.
- A Python step's table is written: its rows built through `query`, saved through `execute`.
- It gives back `results`, each SELECT's DataFrame by its name; nothing saved to a file.
- The first that fails stops the rest and raises, so the notebook fails; before raising it
  prints `START_FROM = "<table>"` to rerun from it, and that every table before it was
  written.
- It writes no lineage and no file of its own; an Admin statement is logged by `run_execute`.
- Tests on the Example database: a run writing three tables and returning a SELECT; a failure
  halfway and its START_FROM rerun; a Python step.

## Answer

Built 2026-11-09.

- `results = built.run(query, execute)`, a method of `scheduled_runs.BuiltRun`, its work in
  `scheduled_runs.run_built`. Your query and execute are checked first, as functions and not
  the other way round (known by their names, as `run_query` knows a swap), before anything is
  sent. Each step goes in the build's order: a SELECT through `run_query`, its rows in
  `results` by the step's `result` name; a write, create, upkeep, Admin or Unchecked statement
  through `run_execute`, so an Admin or Unchecked statement is logged in the Admin log, and
  `admin/sent.csv` gets its row, as anywhere. It gives back a plain dict and saves nothing to
  a file; it writes no lineage.
- Its lines are `run_tables`' lines, **numbered as the build numbered its headings**, so a
  rerun from START_FROM goes on at `3 of 4`: `2 of 4: mart.team_jobs   worked`, a SELECT's
  `worked: 4 rows, in results["jobs"]`, a Python step's `worked: 4 rows saved`, and a last
  line, `Sent 4 Statements in order. results holds the rows of jobs, by name, as
  results["jobs"].`
- "dynamic_partitions" is sent once first when a write fills Partitions from its rows
  (`settings_needed`, as `run_tables` asks it) or a Python step saves to a partitioned table;
  a table's `session_settings()` before its first write, and again after another table's
  write, the rule `_print_build` prints them by (repeated in `run_built`, not shared, so ticket
  05's work on the build merges plainly).
- **A Python step's rows come from a new `rows=` on `python_step`**, the SELECT its function
  takes, such as the Table notebook's `rows()`: a `PythonStep` didn't hold the rows' SELECT, nor
  its function, and today its own notebook pulls the rows with `run_query(rows(), query)` and
  saves them with the user's own API (the how-to's `my_api.write_table`), which the Toolbox
  can't call. `PythonStep` now keeps its function and `rows=`; `rows=` is refused unless it is
  a read or an Unchecked statement. **One with no `rows=` is refused before anything is sent**,
  naming its table and the fix (`rows=rows()`, or `leave_out=` and its own notebook).
- **The rows are saved by Hive the Toolbox writes from them, `python_steps.saving_hive`**:
  `INSERT OVERWRITE TABLE t PARTITION (p) SELECT stack(n, ...) AS (columns)`, each value
  `CAST(... AS <its column's type>)` written through `literal`, a missing value `CAST(NULL AS
  ...)`, the partition columns last, so each Partition the rows fill is written again and a
  rerun is safe. It is sent through your execute itself, not as an Unchecked statement, so the
  rows aren't copied into the Admin log. Refused: what the function gives back that isn't a
  DataFrame, rows lacking a column of the table or holding one it hasn't, and a value that
  doesn't fit its column (a cast Hive can't make saves NULL with no error). No rows send
  nothing, and the line says so. `show_hive` of a step with `rows=` says a Scheduled run saves
  its rows; without, as before.
- **The first that fails** prints `failed: see below. The Statements after it weren't sent.`,
  the tables this run wrote before it, and `START_FROM = "<table>"`, then raises the original
  error. The table is the failed step's own; **for a step that writes none, a SELECT, the
  table whose first write comes last before it**, so the rerun sends the SELECT again (`""`
  when none comes before it).
- Tests: `tests/test_built_run.py`: three tables and a SELECT, with no file written but
  `sent.csv`'s rows; a failure halfway and its START_FROM rerun; a failed SELECT's START_FROM;
  a Python step's table written, through a partitioned table's dynamic_partitions; one with no
  `rows=`, and rows lacking a column; NULL, a timestamp, no rows and a value that doesn't fit;
  `rows=` refused; query and execute swapped; and `built.run`'s docstring example, which
  `tests/test_docstrings.py` doesn't run, as it isn't a public name. The gallery,
  `examples.html`, picks that example up as `scheduled_runs.BuiltRun.run`.
- Left: the how-to "Declare a change made in Python", the README and Copilot file 18 don't yet
  show `rows=` or `built.run` (ticket 10). CONTEXT.md's Python step now says a Scheduled run
  writes one's table.

### The code review (2026-11-09)

The review of ticket 06, mended in `fix(8.6): tickets 05 and 06's code review, and D481`:

- **Decided: a SELECT that fails reruns from itself.** `START_FROM` now names a table, whose
  first write the rerun starts from, or a SELECT, by its name (`RunStep.start_from_name`, its
  table or its `result`); a table is looked for first. The failed SELECT prints
  `START_FROM = "busiest"`, so the rerun sends no write before it again, and an `INSERT_INTO`
  before it can't add its rows twice. The build's passed-over line says `before it` for a
  SELECT, `before its first write` for a table. A name no step writes and no SELECT has is
  refused, naming both. Only a failed step with neither, an Admin or Unchecked statement
  writing no table, still names the table whose first write comes last before it
  (`_last_table_first_written_before`), as no name reaches it. Test:
  `test_a_failed_select_reruns_from_itself_sending_no_write_again`. `build_run`'s docstring,
  `built.run`'s, the scheduled_run Template's `START_FROM` comment and CHANGES.md say so.
- One rule for a table's Session settings: `scheduled_runs.settings_before_each(built)`, the
  settings sent before each step, which `run_built` sends and the build prints (and
  `step_texts`, ticket 08's). `last` is `last_table_written` there. `_rerun_lines`' own
  first-write search is `_last_table_first_written_before`, and its docstring now says what
  it gives. `RunStep.heading` gives the heading without `--`; the build prints `-- ` before
  it, and lists a step passed over by it as it is.
- `kinds.kind(step.statement) == kinds.PYTHON` is `RunStep.is_python_step`.
- What callers need of a `PythonStep` are functions of `python_steps.py`, as `step_where` and
  `step_columns_read` are: `step_rows`, `is_partitioned`, and `changed_rows`, which calls the
  step's function and checks what it gives back, so `saving_hive` now takes a checked
  `pd.DataFrame`. Answered, not changed: methods on `PythonStep` would show in its `help()`,
  a public class; and `saving_hive` lives beside `PythonStep`, so its fields are that module's
  own, while a Table's `_columns` and `_partitioned_by` are read as its fields throughout the
  Toolbox, which has no other way to them.
