# The Spark printer, flat: values, names, expressions and the read-back check

Type: task
Status: open
Blocked by: 16

Findings: [ticket 04](../findings/04-spark-reads-the-hive.md) gives the evidence and wording
this ticket uses.

## Question

Write `spark_composer/writing.py`'s one-line output. It imports only the standard library and its
own package, and dispatches through one dict of kind to function, so each function stays within
ruff's C901 limit of 10.

It writes, matching sqlglot 30.19.0's Hive byte for byte except for declared rows:

- string escaping as `tests/escaping_cases.py` pins it, numbers as the Toolbox formats them, and
  backticks with doubled backticks;
- every expression kind, flat, with sqlglot's spellings (`NOT x IN (...)`, `NOT x IS NULL`,
  `COUNT(DISTINCT ...)`, `ROW_NUMBER() OVER (...)`, `CASE WHEN ... END`);
- the printed forms of the five Toolbox date calls (date_sub prints as `DATE_ADD(x, n * -1)`);
- hive_function as given, its name upper-cased: the first declared difference;
- `a / NULLIF(b, 0)` when dividing by anything but a non-zero number: the second declared
  difference (ticket 04: Spark raises on a zero divisor under ANSI, a literal 0 included);
- a float as a DOUBLE literal, `0.5D` where SQL Composer writes `0.5`: the third declared
  difference (ticket 04: Spark reads `0.5` as DECIMAL, which pandas shows as `Decimal`).

It also provides `read_back_function` (checked against the shared argument table and aggregate
list), `describe_text`, `show_partitions_text`, and `read_back(text)`, a lexical check: one
statement, no comment or `;` outside a literal, and every literal and quoted name decodes to what
was written. In `tests/`, an independent lexical literal reader replaces sqlglot's `_literals`, so
the escaping-through-the-Toolbox tests run in both Editions.

## Done when

The Definition of done in `CLAUDE.md` holds; every flat repr and readable case matches the sqlglot
golden except declared rows; the escaping tests pass in both runs; a deliberately broken quote
escape in a test copy makes `to_hive` refuse with "bug in the Toolbox, nothing was sent"; the
default run is green.
