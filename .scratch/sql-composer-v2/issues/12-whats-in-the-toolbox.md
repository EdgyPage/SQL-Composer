# What's in the Toolbox?

Type: grilling
Status: resolved
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

## Answer

**59 public names in eight flat modules.** Every name is imported from the top
(`from sql_composer import ...`), so the module split exists only for reading.

| module | holds |
| --- | --- |
| `__init__.py` | re-exports, `VERSION`, the file-list and version self-check, the sqlglot version check |
| `tables.py` | `Table`, `write_table_reference`, `first_look`, `check_key`, `create_table`, `all_columns` |
| `clauses.py` | `SELECT`, `SELECT_DISTINCT`, `AS`, `FROM`, `JOIN`, `LEFT_JOIN`, `CROSS_JOIN`, `WHERE`, `GROUP_BY`, `HAVING`, `ORDER_BY`, `LIMIT`, `INSERT_OVERWRITE`, `statement`, `derived` |
| `conditions.py` | `equals`, `not_equals`, `is_null`, `is_not_null`, `at_least`, `at_most`, `more_than`, `less_than`, `between`, `last_n_days`, `is_in`, `is_not_in`, `contains`, `starts_with`, `any_of`, `all_of` |
| `calculations.py` | `count_rows`, `count_distinct`, `sum_of`, `average_of`, `min_of`, `max_of`, `if_else`, `fill_null`, `week_start`, `month_start`, `row_number`, `descending`, `hive_function` |
| `running.py` | `to_hive`, `run`, `by_day`, `set_load_limits` |
| `refusals.py` | every Guard and Load limit in one file, with `GuardRefused` and `LoadRefused` |
| `lineage.py` | `export_lineage` and the graph layout |

**Decided here:**

- **Naming a table twice:** `AS(job_runs, "earlier")` returns a checked copy called `earlier` in
  the SQL, as in `FROM job_runs AS earlier`. Two tables with the same short name in one Statement
  refuse at `statement(...)`, and the message names this fix. The copy counts as its own table for
  the Load limits, so its date partition must be bounded too.
- **`check_key(t, send=...)` stays.** It runs one bounded day (`GROUP BY key HAVING COUNT(*) > 1
  LIMIT 20`) and returns a verdict: "key holds on 2026-09-24", or the duplicates. It protects the
  premise of the repeated-rows Guard.
- **Conditions:** `at_least`, `at_most`, `more_than`, `less_than`; `all_of` for AND inside an
  `any_of`; `is_in(col, values)` / `is_not_in(col, values)` for `IN`, with `NOT IN`'s NULL trap
  closed by the `None` Guard; `contains` and `starts_with` for `LIKE`, escaping `%` and `_`. There
  is no `not_(...)`, since every condition comes with its own opposite.
- **Aggregates:** `sum_of`, `average_of`, `min_of`, `max_of`, `count_distinct` and `count_rows`,
  lower case and suffixed so they never shadow Python's `sum`/`min`/`max`. Conditional counts are a
  keyword, not a function: `count_rows(where=...)`, `sum_of(col, where=...)`. The `adds_up=True`
  opt-out sits on `sum_of` and `average_of`.
- **Row-level calculations:**
  - Arithmetic uses Python's `+ - * /` on columns, since Python's precedence matches SQL's and the
    tree comes out bracketed. `==`, `<`, `&` and the like on a column **raise immediately** and
    point to `equals(...)`, which catches Style A's silent `WHERE FALSE` at the call.
  - There is no `safe_divide`: Hive's `/` returns `NULL` on a zero divisor and never divides
    integers, and the docstring says so. A division already counts as "does not add up".
  - `if_else(condition, then, otherwise)` gives `CASE WHEN`, and `fill_null(col, value)` gives
    `COALESCE`.
  - `week_start` (Monday) and `month_start` are the only date buckets. Anything else goes through
    `hive_function`.
- **`newest_first` is renamed `descending`,** which reads right on any type.
- **New clauses:** `HAVING` and `SELECT_DISTINCT`. `UNION_ALL` goes to the fog.
- **No pattern functions.** Latest row per key and top N per group are two `derived` calls around
  `row_number`, shown in `row_number`'s docstring and in the example database.
- **`export_lineage(*statements, to="lineage.html")`** writes the HTML and its script-free
  Markdown twin side by side, both stamped with `VERSION`, joining Statements across Saved tables.
- **`set_load_limits(rows=None, dates=None)`** switches the two seams on from the user's own
  notebook, because a constant edited inside `sql_composer/` would be undone by the next update.
  An argument left out means no limit, so `set_load_limits()` switches both off. It returns the
  values in force and refuses nonsense such as `rows=-1`.
- **Other mistakes use Python's own exceptions.** A typo'd column raises `AttributeError` (so
  `hasattr` behaves normally), and misuse raises `TypeError`/`ValueError` with the four-part
  message. The `to_hive` self-check raises `RuntimeError` and says it is a Toolbox bug, not the
  user's. `GuardRefused` and `LoadRefused` stay the only Toolbox exceptions.

**Docs:**

- **Every docstring carries one worked example:** a `>>>` call on the example database's Table
  references (`job_runs`, `jobs`) and the exact Hive it emits, ready to run as a doctest.
- **The Clean branch README gets a cheat sheet:** one line per name, grouped by module, generated
  from each docstring's first line. This is the one-sitting read. No name was cut, because each
  candidate would come back as a `hive_function` call or a workaround.

**What the user could just as well write in plain Python or plain Toolbox calls:**

- latest-per-key and top N per group, as two `derived` calls around `row_number`;
- `first_look(t)`, which is an ordinary bounded Statement;
- lists of columns of interest and site codes, which are plain Python lists;
- the `by_day` loop, which is a plain `for` loop;
- sorting a result, which is done in pandas after `run`, not in `ORDER_BY`.

Handed on:

- **"What does `dev` enforce, and which maintainer agents does it carry?"** It decides whether
  the docstring examples run as doctests, and adds a check that the generated cheat sheet is up to
  date.
- **"What does the example database demonstrate, and where does it run?"** The docstrings use
  its `job_runs` and `jobs` Table references, so those two tables must exist under those names.
- **"What does exploring a Statement's lineage look like?"** It gets the `export_lineage`
  signature.
- **The map:** `UNION_ALL` joins the fog. The core build graduates into "Retire v1 from `dev`
  and carry over the salvage" and "Build the Toolbox core".

**Changed by "What does the Example database demonstrate, and where does it run?" (2026-09-25).**
A 60th public name, `example_database`, ships the Example database inside the Toolbox as a
sandbox. The repeated-rows check became a Warning; its category isn't a public name.
