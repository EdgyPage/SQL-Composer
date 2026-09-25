# Build the Toolbox core

Type: task
Status: resolved
Blocked by: 16, 17

## Question

Build `sql_composer/` as decided in "What's in the Toolbox?": every module except `lineage.py`,
with its 58 names (all 59 except `export_lineage`), each with a doctest-ready worked example on
the example database's `job_runs` and `jobs` Table references.

The governing decisions, each in its own ticket:

- **"How does a composed Statement read?":** the clause-function shape, named calculations, and
  `GROUP_BY` on an output name;
- **"Which guardrails on how a Statement is written earn their place?":** the Guards,
  `GuardRefused`, the four-part message and the `to_hive` self-check;
- **"How much may a Statement touch and return by default?":** the Load limits, `LoadRefused`,
  `run` and `by_day`;
- **"How do pieces combine across Levels - CTE, subquery, or saved table?":** Derived tables as
  CTEs, `INSERT_OVERWRITE` and `create_table`;
- **"What goes in a Table reference, and is it written or generated?":** `Table`,
  `write_table_reference` and `first_look`;
- **"Which sqlglot APIs can the Toolbox use at work?":** the supported sqlglot range and the
  import-time checks;
- **"How does the Toolbox survive being pasted over an existing directory?":** the flat package,
  `TOOLBOX_VERSION` and the self-check;
- **"Does the Toolbox check a Table reference against the warehouse?":** any function it adds.

Done when the checks `dev` enforces pass and the Style B prototype Statements
(`prototype/statement-styles`) can be rewritten against the real Toolbox.

## Comments

**From "What does `dev` enforce, and which maintainer agents does it carry?" (2026-09-25).** The
checks this build adds as it goes:

- **Import allowlist:** only the standard library, pandas, numpy, sqlglot and other Toolbox
  modules.
- **Versions:** `TOOLBOX_VERSION` agrees across files, and `CHANGES.md` has a section for it.
- **Doctests:** every docstring example runs as a doctest, with `job_runs` and `jobs` supplied by
  the test setup, and a test fails if a public name has no docstring or no `>>>` example.
- **Readability limits:** the list of 59 public names, each docstring's first line at most 80
  characters, and ruff's C901 at most 10.
- **Refusal coverage:** every Guard and Load limit has one test showing it refuse and one showing
  its opt-out working. One helper builds the four-part message.
- **Pin in range:** the sqlglot pin falls inside the supported range.

The Toolbox's Python floor is 3.11, and the import self-check says so. The ticket's definition of
done applies: `pytest` passes, `code-review` has run against this ticket, there are no open drift
items, and the beginner reader has reported.

**From "What does the Example database demonstrate, and where does it run?" (2026-09-25).**

- **A 60th public name, `example_database`:** the module `sql_composer/example_database.py`. It
  holds the three Table references `jobs`, `job_runs` and `run_alerts`, their rows (from the
  prototype's `example_database/rows.py` on `prototype/example-database`), and a `send` that runs
  Hive on sqlglot's executor and returns a DataFrame. Below sqlglot 30.19.0 that `send` stops
  with a plain message naming the version. The doctests take `job_runs` and `jobs` from it, and
  the name-list test lists 60 names, so this build ships 59 of them.
- **Repeated rows is a Warning, not a Guard.** When `JOIN(T, ON=...)` doesn't pin down T's whole
  key, or T declares no key, the Statement builds and runs. A Python warning at the user's `JOIN`
  line gives the four-part message, and `many_matches=True` silences it. With no key, the message
  also says to declare `key=[...]`.
  - The warning category lives in `refusals.py` and isn't a public name.
  - It must show on every `JOIN` that earns it, not once per line, which is Python's default.
  - Refusal coverage covers it: a test shows it firing, and one shows `many_matches=True`
    silencing it.
- **A Derived table's key is its `GROUP_BY` columns,** so joining a grouped Derived table on them
  raises no Warning.
- **A date bound in `ON` counts.** After `LEFT_JOIN(T)`, the Load limit accepts T's Date
  partition bound inside `ON`, since the `LEFT JOIN` then `WHERE` Guard refuses it in `WHERE`.

**From "Does the Toolbox check a Table reference against the warehouse?" (2026-09-25).**

- **A 61st public name, `check_table_reference(t, send=...)`,** in `tables.py`. It sends
  `DESCRIBE` and `SHOW PARTITIONS` through `send`, reusing `write_table_reference`'s parsing, and
  returns a printable verdict of problems and notes, each with the line to change. It never raises
  and never edits the file. The name-list test lists 61 names; this build ships 60 of them.
- **`create_table(t)` is strict:** plain `CREATE TABLE`, with `may_exist=True` for
  `IF NOT EXISTS`. Its docstring explains Hive's `AlreadyExistsException`.
- **`example_database.send` answers `DESCRIBE` and `SHOW PARTITIONS`** itself, from its own Table
  references and rows, since sqlglot's executor can't. The doctests of `write_table_reference`,
  `check_key` and `check_table_reference` run on it.

**From "Retire v1 from `dev` and carry over the salvage" (2026-09-25).** `dev` now holds no v1
code. The escaping matrix waits in `tests/escaping_cases.py`. Its docstring says how to adopt
it: push every case through each way a value reaches a Statement (each comparison function, both
ends of a range, each item of a list, a Date partition bound, the PARTITION of an
`INSERT_OVERWRITE`), and test the two properties the cases can't: `.sql()` is called in exactly
one function with `unsupported_level=ErrorLevel.RAISE` and SQL text is never built with an
f-string, and a number is formatted by the Toolbox (`SNEAKY_NUMBERS`, `NON_FINITE_NUMBERS`).

**Build decisions (2026-09-25), where the tickets left something open.** Each picks the most
beginner-readable option; the user may overturn any of them.

- **The seams under test are the public names.** Every test goes through `from sql_composer
  import ...` (plus `refusals.py`'s Guard functions for the coverage test), as the tickets
  decided the names; no test reaches into a Statement's parts.
- **The count.** "What's in the Toolbox?" lists 57 functions and classes plus `VERSION`, 58,
  but counts 59. The build reads the 59th as `TOOLBOX_VERSION`, which every file declares and
  `__init__.py` exports. With `example_database` and `check_table_reference` that makes the
  name-list test's 61, of which 60 ship (all but `export_lineage`). **For the user to confirm.**
- **`TOOLBOX_VERSION = "2.0"`,** since this is v2 and no ticket fixed a value (`3.1` in the
  tickets is an illustration). **For the user to confirm.**
- **The two constants' docstring is the Toolbox's own** (`sql_composer.__doc__`), since a
  string can't carry one; its `>>>` example shows both.
- **`last_n_days(col, n)` writes the dates,** worked out when it is called: the n days before
  today, today excluded, as `BETWEEN 'first' AND 'last'` (`=` for one day; `>=`/`<` on a
  `timestamp` column). The Hive shows which days are read, partition pruning is certain,
  `by_day` and the dates cap can count them, and it's the same on every sqlglot. A Statement
  built at import keeps that day's dates until rebuilt.
- **`week_start` is `NEXT_DAY(DATE_SUB(d, 7), 'MO')`,** which sqlglot writes as
  `NEXT_DAY(DATE_ADD(d, 7 * -1), 'MO')`; the usual `DATEDIFF` form doesn't read back the same
  on sqlglot 25.24.2. `month_start` is `TRUNC(d, 'MM')`. On a Date partition with another
  `date_format`, both first turn the day into `yyyy-MM-dd`.
- **All six aggregates take `where=`,** not only `count_rows` and `sum_of`, so there is one rule.
- **`LEFT_JOIN` takes `many_matches=` too,** since it repeats rows the same way. `is_null` on
  the LEFT_JOIN's table in `WHERE` is allowed: it is the usual "rows with no match".
- **A Derived table's key:** its `GROUP_BY` columns; all its columns after `SELECT_DISTINCT`;
  none needed (one row) when it aggregates with no `GROUP_BY`; and its table's key when it only
  filters one table and keeps the key columns. Joining on it then warns only off that key.
- **`statement(...)` wants its clauses in SQL order,** one of each except joins, with `SELECT`
  and `FROM` required.
- **Misuse checks beyond the Guards,** as `TypeError`/`ValueError` with the four-part message:
  a column of a table the Statement doesn't read; two output columns with one name; a count in
  `WHERE` (points to `HAVING`); a Date partition value that isn't a day in its `date_format`;
  `between` with its days reversed; an empty `is_in`; a value of the wrong type for a typed
  column.
- **`check_key` checks the newest day from `SHOW PARTITIONS`** (a table with no Date partition
  is checked whole), and names its count `copies`. It and `check_table_reference` return a
  result that prints as plain lines and has `.ok`.
- **`write_table_reference`** writes into the folder you're working in and returns the path;
  it recognises days written `%Y-%m-%d`, `%Y%m%d` or `%Y/%m/%d`.
- **`create_table` returns a Statement, not a string,** so `run(create_table(t), send=...)`
  sends it and there is still no raw-SQL entry point.
- **`INSERT_OVERWRITE` needs a real table with a Date partition,** and a write whose FROM table
  has no date bound is refused at `to_hive` (the day to write isn't known).
- **`hive_function` reads its call back once,** so a function sqlglot rewrites (DATEDIFF on
  25.24.2) comes out in the form the self-check will see; `nvl` comes out as `COALESCE`.
- **Names that are Hive reserved words** (`user`, `select`, ...) are written in backticks.
- **`example_database.send`** answers `DESCRIBE` and `SHOW PARTITIONS` on any sqlglot, runs
  queries only on 30.19.0 or newer after a `COUNT(DISTINCT)` known-answer check, and refuses
  writes.
- **The import self-check on `dev`:** `_FILES = None` until the export writes the list, so
  the missing/extra checks wait for the Clean branch; the version and export-stamp checks run
  everywhere. `VERSION` reads the export stamp, or says `not exported (dev)`. A sqlglot newer
  than 30.19.0 prints a one-line note.

**Found, not from this build:** `tests/test_escaping_cases.py::test_a_quoted_identifier_stays_one_name`
fails on sqlglot 25.24.2 for the two backtick cases (its parser can't read a doubled backtick
back), so CI's 25.24.2 run was already red on `dev`. The Toolbox writes such names correctly on
both ends, but on 25.24.2 its self-check would stop a Statement that uses one.

**Code review (2026-09-25), `code-review` over `d0cf695..HEAD`,** with this ticket and the
tickets it names as the spec and `docs/agents/standards.md` as the standards. What was fixed,
and what is answered here instead:

- **Fixed, Standards:**
  - `date_column` (an _Avoid_ word for Date partition) renamed to `date_partition` in
    `guard_by_day_grouping` and `by_day`'s checks.
  - "level", which the glossary keeps for the tiers of the user's scripts, no longer names a
    Derived table's depth in `running.py`, nor appears in the re-grouping fix ("divide after
    your own `GROUP_BY`").
  - "query" became Statement in `set_load_limits`, the dates cap's message and `CHANGES.md`.
  - The `derived` docstring no longer says "checked attributes", "WITH part" or "Statement
    part".
  - `first_look`'s first line says yesterday, as the code does.
  - `average_of` now names its `adds_up=True` opt-out, as `sum_of` does.
  - Names no ticket decided are private: `_SQLGLOT_LOWEST`, `_SQLGLOT_BELOW`,
    `_SQLGLOT_NEWEST_TESTED`, and `example_database`'s `_COMMENTS`, `_JOBS`, `_JOB_RUNS`,
    `_RUN_ALERTS`, `_TABLES` and `_EXECUTOR_NEEDS`. The import messages build the sqlglot
    range from the constants.
  - Cheap smells: `_parse_day` is `_day_format_of`, `running.py`'s `_join` is `_join_tree`,
    `Ordering` no longer stores a flag it never reads, and `_aggregate` takes `distinct=True`,
    not `kind="distinct"`.
- **Fixed, Spec:**
  - `check_table_reference` never raises on the warehouse's side any more. A table `DESCRIBE`
    can't find, or a `send` that fails, comes back as a failed verdict that quotes the error.
    A `SHOW PARTITIONS` that fails comes back as a problem.
  - A `date_format` that is back to the usual days now says to remove the `date_format` line.
    Before, it said to write `date_format="%Y-%m-%d"`.
  - `ORDER_BY`'s Load limit offers `sorts_everything=True` "but not in a Statement you pass to
    `derived(...)`". Before, pasting that opt-out inside a Derived table led only to a second
    refusal.
  - `example_database.send`'s own messages have the four parts. When sqlglot's executor
    can't run something, it stops with a plain message naming it: window functions such as
    `row_number`, or `NEXT_DAY` and `TRUNC` from `week_start` and `month_start`. Before, it
    raised a raw `ExecuteError`. Ticket 15 already decided that those demonstrations show
    pandas results.
  - `example_database.send` now matches `starts_with` and `contains` correctly. The
    executor ignores `LIKE`'s backslash, so `starts_with(jobs.job_name, "invoice_")` found no
    rows. `send` now spells an escaped `LIKE` out as `LEFT`, `RIGHT` or `STRPOSITION`. This
    was found by the beginner reader.
  - The import check's behaviour-check refusal and the newer-sqlglot note now have tests.
  - The Style B test now also writes the prototype's own boolean `is_active` and timestamp
    `started_at` Statement, on the prototype's own Table references.
  - The review also noted `refusals.py`'s docstring (it now says where each check stops) and
    `row_number`'s claim about the Example database. That docstring now shows the latest run
    per job itself, through `to_hive`, since the executor has no window functions.
- **Answered, not changed:**
  - **`ORDER_BY` without `LIMIT` inside a Derived table is a `GuardRefused`,** though ticket
    09 lists it with the Load limits. What it protects is the answer: Hive silently drops the
    order, and the cluster isn't at risk. The glossary says a check that protects the answer
    is a Guard. An `ORDER_BY` with a `LIMIT` inside a Derived table is allowed, since ticket
    09's rule is "no `ORDER BY` without a `LIMIT`" and Hive keeps that order. **The user may
    overturn this.**
  - **`hive_function("regexp_extract", col, pattern, 1)` comes out without the `1`.**
    sqlglot's generator drops the group when it is 1, Hive's default, so the Hive means the
    same. Fighting the generator would break the `to_hive` self-check. The docstring now says
    so.
  - **Misuse errors print "Opt-out: none".** "Build decisions" gives every misuse check the
    four-part message, and ticket 08 says every message has four parts, so the line stays.
  - **`check_table_reference` still raises `TypeError` for a non-Table or a Derived table.**
    That is calling it wrong. Ticket 16's "never raises" is about what it finds in the
    warehouse.
  - **`sum_of(..., adds_up=False)` in the signature** can read as "doesn't add up". Tickets
    08 and 12 fixed the keyword, and every opt-out defaults to `False`. Each docstring says
    to pass `adds_up=True` if the column really does add up.
  - **Smells left, since standards.md prefers plain repetition to cleverer machinery:**
    - `_need_column` is written twice, `_conditions` twice, and version parsing twice;
    - the "db.table" split is written three times;
    - opt-out text is built by slicing `call[:-1]`;
    - several functions branch on `Clause._name` and on whether `_statement` or `_ddl` is set;
    - `derived` sets a `Table`'s private fields;
    - `_select_tree` reads a Statement's parts;
    - `tables.py` has in-function imports that avoid a circular import.

    None of these shows through a public name, and each one is small.
  - **`more_than` and `less_than` count as a date bound at both ends,** where ticket 09 lists
    only `>=` with `<=`. Either pair bounds the partition, so it stays.

## Answer

**The Toolbox core is built: `sql_composer/` ships 60 of the 61 public names, everything but
`export_lineage`, which "Build `lineage.py`" adds.** Commits 0089c86, d3eb535, e9bbfc7 and
30a2af0.

- **Modules**, flat in `sql_composer/`, each declaring `TOOLBOX_VERSION = "2.0"`:
  - `__init__.py`: `TOOLBOX_VERSION`, `VERSION` and the import self-check. The self-check
    covers the Python floor 3.11, sqlglot from 25.24.2 up to (not including) 31 with three
    behaviour checks, mixed versions and export stamps, and missing or extra files once the
    export writes `_FILES`.
  - `tables.py`: `Table`, `write_table_reference`, `first_look`, `check_key`,
    `check_table_reference`, `create_table` and `all_columns`.
  - `clauses.py`: the clause functions, `statement` and `derived`.
  - `conditions.py`: the named comparisons, `last_n_days`, `any_of` and `all_of`.
  - `calculations.py`: the `_of` aggregates, `if_else`, `fill_null`, `week_start`,
    `month_start`, `row_number`, `descending` and `hive_function`.
  - `running.py`: `to_hive` with its self-check, `run`, `by_day` and `set_load_limits`.
  - `refusals.py`: every Guard, Load limit and the repeated-rows Warning, with `GuardRefused`,
    `LoadRefused` and the one four-part message.
  - `example_database.py`: `jobs`, `job_runs`, `run_alerts` and a `send` on sqlglot's
    executor.
  - `CHANGES.md`: the 2.0 section.
- **Tests:** 609, all passing on sqlglot 30.19.0. They check:
  - every docstring as a doctest, with a short first line;
  - the 61-name list and the import allowlist;
  - `TOOLBOX_VERSION` across files and in `CHANGES.md`;
  - ruff with C901 at most 10, and the sqlglot pin in range;
  - a refusal and an opt-out for every Guard, Load limit and the Warning;
  - the escaping matrix through every way a value reaches a Statement;
  - the import self-check, Table references, whole Statements and the Example database;
  - the Style B prototype's Statements, rewritten.

  On sqlglot 25.24.2, the two backtick cases of `test_escaping_cases.py` still fail. They
  failed before this build, which is noted above.
- **Decisions:** "Build decisions" above records where the tickets left a choice open. Two of
  them are **for the user to confirm**:
  - the 59th name is read as `TOOLBOX_VERSION`;
  - `TOOLBOX_VERSION` is `"2.0"`.

  The code review above records what was fixed and what was answered. One of the answers is
  also the user's to overturn: `ORDER_BY` without `LIMIT` inside a Derived table is a
  `GuardRefused`, not a `LoadRefused`.
- **Drift:** D5 opened and closed, and nothing is open.

Beginner reader: .scratch/sql-composer-v2/reports/18-beginner-reader.md

The report is advice for the user. The code review fixed its two bugs:
- `LIKE` escapes on the Example database;
- raw executor errors for `row_number` and `week_start`.
