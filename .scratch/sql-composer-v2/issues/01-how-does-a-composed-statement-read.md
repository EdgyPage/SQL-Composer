# How does a composed Statement read?

Type: prototype
Status: resolved
Blocked by: -
Prototype: branch `prototype/statement-styles` (commit `b1f5e8c`), `prototypes/statement_styles/statement_styles.html`

## Question

Readability for a Python-first SQL beginner is the top priority, and most other tickets hang off
this one. Make the question concrete. Pick two or three realistic queries of the kind the user
will write - for example: a count of failed rows by week and by one attribute over the last N
days; a two-table join narrowed by a filter that comes from a Building block; the latest row per
key. Write each in two or three candidate styles, across all three Levels (the Table reference it
uses, the Building block it borrows, the Statement itself), and show the Hive string each emits.

Candidate styles to include at minimum: a thin layer over sqlglot's own builder; clause functions
that return pieces, in the user's words "SELfunc(params) FROMfunc(params)"; and whatever else the
prototype suggests. Put them side by side and let the user react and choose.

The choice fixes the vocabulary every later ticket uses: how a column is referenced, how a
Building block plugs into a Statement, and how a Statement becomes a string.

## Answer

**Clause functions (style B), with C's guarantees added.** A Statement is a list of clause functions
written in SQL order, and it becomes a string through `to_hive(...)`:

```python
week = week_start(runs.dt)

failed_by_week = statement(
    SELECT(AS(week, "week"), runs.region, AS(count_rows(), "failed_runs")),
    FROM(runs),
    WHERE(failed_runs(), last_n_days(runs.dt, 30)),
    GROUP_BY(week, runs.region),
)
hive = to_hive(failed_by_week)
```

- **A column is referenced** as an attribute of its Table reference, `runs.status`. A typo fails in
  Python with the table's column list.
- **Conditions are named functions**, not operators: `equals(runs.status, "FAILED")`,
  `not_equals(...)`, `any_of(...)`. `WHERE(...)` joins its arguments with AND.
- **A Building block plugs in as a plain function return.** A filter block returns a condition (or a
  list of conditions), and a join block returns the `ON` condition for `JOIN(table, ON=...)`. A
  sub-query block returns a named Statement, `derived("latest", statement(...))`, whose output
  columns are checked attributes (`latest.status`), exactly like a Table reference's.
- **A Statement becomes a string** through `to_hive(statement)`, which uses sqlglot underneath. sqlglot
  never appears in the user's scripts.

The user found B the most legible and C (pandas-flavoured: `==`, `&`, `|`, one `query(...)`
call) a close second. They would take C only if it scaled better with stronger guarantees and no
pandas/SQL/string conversion issues. Probing both styles (`probe_values.py`) showed that it doesn't:

- Value conversion is identical in B and C (both go through `sqlglot.exp.convert`), so its flaws
  don't separate them.
- C adds a silent trap that B can't have: `(a == 1) & b == 2` emits `(a = 1 AND b) = 2`, because `&`
  binds tighter than `==`. C also can't use Python's `not` or `in`.
- C's extra guarantees came from its Toolbox, not its shape, so B takes them over:
  1. **Every calculation must be named.** `SELECT` refuses a calculation without `AS(...)`, which
     would otherwise reach pandas as a column called `_c1`. Plain columns keep their own name.
  2. **`GROUP_BY` may name an output column** (`GROUP_BY("week", runs.region)`), and the Toolbox
     repeats the calculation, since Hive can't group by an alias.
  3. **Sub-query columns stay checked** through `derived(...)`.

Styles ruled out, and why:

- **A, sqlglot's own chain:** writing `==` instead of `.eq()` silently emits `WHERE FALSE`.
- **D, SQL text:** a block containing `OR` pasted in without brackets silently escapes the date
  filter and reads every partition, and sub-query columns aren't checked.

What this leaves for later tickets:

- **Value-conversion traps,** handed to "Which guardrails on how a Statement is written earn their
  place?":
  - `equals(col, None)` emits `= NULL`, which matches nothing.
  - `NaN` becomes `NULL`.
  - A numpy `True` crashes.
  - `pd.Timestamp` becomes `CAST(... AS TIMESTAMP)`, which may defeat a string partition filter.
- **sqlglot rewrites what is sent.** `DATE_SUB(dt, 30)` goes out as `DATE_ADD(dt, 30 * -1)`: valid,
  but not what was written.
- **Where a sub-query lands** (explicit `WITH(...)`, inlined, or a saved table) is left to "How do
  pieces combine across Levels - CTE, subquery, or saved table?". The prototype tried both explicit
  and automatic `WITH`.
- **Upper-case clause names** (`SELECT`, `FROM`) are kept for legibility despite PEP 8. Callables
  like `count_rows`, `week_start` and `equals` stay lower-case.
