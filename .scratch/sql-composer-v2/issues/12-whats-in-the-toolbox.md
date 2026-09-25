# What's in the Toolbox?

Type: grilling
Status: claimed
Blocked by: 01, 08, 09, 10

## Question

With the syntax, the guardrails, the load behaviour and the way pieces combine all settled, fix
the function list:

- the clause functions - the user's "SELfunc(params) FROMfunc(params)";
- calculations - date bucketing, safe division, conditional counts;
- common patterns - latest row per key, top N per group;
- the output side - to a Hive string, to a lineage HTML file.

Every function ships with a worked example in its docstring. Keep the count small enough to read
in one sitting, and note anything the user could just as well write in plain Python.

## Comments

**From "How does a composed Statement read?"** The vocabulary is fixed:

- clause functions `SELECT`, `AS`, `FROM`, `JOIN(table, ON=...)`, `WHERE`, `GROUP_BY`, `WITH`,
  assembled by `statement(...)` and emitted by `to_hive(...)`;
- conditions `equals`, `not_equals`, `any_of`;
- `derived(name, statement)` for sub-queries;
- calculations `count_rows`, `week_start`, `last_n_days`, `row_number(PARTITION_BY=, ORDER_BY=)`,
  `newest_first`.

Style B's prototype Toolbox (branch `prototype/statement-styles`, `b_clause_functions/toolbox.py`)
is the starting point.

**From "How does the Toolbox survive being pasted over an existing directory?" (2026-09-25).** The
Toolbox is a flat package folder, `sql_composer/`, with a few modules and no subfolders. Users
import only from its top level. Deciding what goes in the Toolbox also decides how it splits into
modules: fewer files make a text paste cheaper, and each module should be named for what a beginner
would go looking for.

**From "Which guardrails on how a Statement is written earn their place?" (2026-09-25).** The Guards add these to the Toolbox:

- `is_null`, `is_not_null`, `LEFT_JOIN` and `CROSS_JOIN`;
- `hive_function(name, *args)`, a generic call that escapes its arguments. It replaces any raw-SQL
  entry point, which the Toolbox doesn't have;
- one exception type, `GuardRefused`;
- the round-trip self-check inside `to_hive`.

`JOIN` requires `ON`. The opt-out keywords are `many_matches=True` (`JOIN`), `adds_up=True`
(`SUM`/`AVG`) and `keeps_only_matches=True` (`LEFT_JOIN`).

**From "How much may a Statement touch and return by default?" (2026-09-25).** Load limits add these
to the Toolbox:

- `run(s, send=...)`, where `send` is the user's function from string to DataFrame, and
  `by_day(s)`, which returns single-day Statements;
- `all_columns(t)`, `LIMIT(n)` and `ORDER_BY(...)`;
- a second exception type, `LoadRefused`;
- two constants that ship unset: an automatic row `LIMIT` and a cap on dates per query.

The opt-out keywords are `reads_all_partitions=True` (`FROM`/`JOIN`), `sorts_everything=True`
(`ORDER_BY`) and `returns_all_rows=True` (`statement`). There's no `OFFSET`, no `*` and no preview
function.

**From "How do pieces combine across Levels - CTE, subquery, or saved table?" (2026-09-25).** Combining pieces adds:

- `derived(name, statement)`: always emitted as a CTE the Toolbox writes, never a `WITH` clause;
- `INSERT_OVERWRITE(table_ref)` as a first clause, one day per write, with no `INSERT_INTO`;
- `create_table(table_ref)`, run once per Saved table;
- a lineage export that takes several Statements and joins them where one writes a table another
  reads.

**From "What goes in a Table reference, and is it written or generated?" (2026-09-25).** Table
references add:

- `Table(name, columns={...}, date_partition=..., key=None, does_not_add_up=[], date_format=None)`,
  which checks itself when it's imported;
- `write_table_reference(name, send=...)`, which writes a new Table reference file from `DESCRIBE`
  and `SHOW PARTITIONS` and refuses to overwrite;
- `first_look(t)`, a Statement of all columns, the last day and 20 rows. It is an ordinary
  bounded Statement, not a preview function;
- `SELECT` and `any_of` accept a list as well as separate arguments.

Still to decide here:

- **naming a table twice in one Statement.** The SQL calls a table by its short name, so a
  self-join, or `ops.jobs` with `mart.jobs`, needs a second name;
- **whether `check_key(t, send=...)` earns its place.** It would confirm a declared key over one
  bounded day.
