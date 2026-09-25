# What's in the Toolbox?

Type: grilling
Status: open
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
