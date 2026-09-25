# Build the Toolbox core

Type: task
Status: claimed
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
