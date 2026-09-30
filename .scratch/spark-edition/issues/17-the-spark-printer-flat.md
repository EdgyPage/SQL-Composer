# The Spark printer, flat: values, names, expressions and the read-back check

Type: task
Status: resolved
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

It also provides `function_adds_rows_up` (checked against the shared argument table and aggregate
list), `describe_text`, `show_partitions_text`, and `read_back(text)`, a lexical check: one
statement, no comment or `;` outside a literal, and every literal and quoted name decodes to what
was written. In `tests/`, an independent lexical literal reader replaces sqlglot's `_literals`, so
the escaping-through-the-Toolbox tests run in both Editions.

## Done when

The Definition of done in `CLAUDE.md` holds; every flat repr and readable case matches the sqlglot
golden except declared rows; the escaping tests pass in both runs; a deliberately broken quote
escape in a test copy makes `to_hive` refuse with "bug in the Toolbox, nothing was sent"; the
default run is green.

## Answer

`spark_composer/writing.py` writes a Statement's Hive with Python's standard library alone
(`ec2b4ef`, answered in `baa3052`).

- **What it writes.** The Hive SQL Composer writes, flat and laid out, the layout ported from
  sqlglot 30.19.0 ahead of ticket 18. Over the golden corpus, 363 of 378 cases show the same in
  both Editions. The other 15:
  - 10 are the three declared differences: NULLIF around a divisor that could be 0 (2 cases),
    a float as a DOUBLE, `0.5D` (2), and hive_function written as named (6);
  - 5 wait for ticket 25, which makes SQL Composer check the same way: create_table's strict
    types refuse json, uuid, interval and `bigint unsigned` (4), and hive_function's arguments
    are counted by `HIVE_FUNCTION_ARGUMENTS` in trees.py, so the refusal reads differently (1).
- **The check.** Each value and backticked name is read back by its characters as it is
  written, with a reader kept apart from the escapes, and must give back what was written; if
  not, `to_hive` stops with "bug in the Toolbox, not in your Statement: nothing was sent".
  `read_back(text)` then holds the whole text to one statement: no comment, `;` or double quote
  outside a value, and every value and name ends.
- **`readable_text`,** new in both Editions' interface: the Hive for the lineage's "as written"
  text. Spark Composer's leaves NULLIF and the D out, so a formula and a Toolbox call's text read
  the same in both Editions; only the Hive differs.
- **Shared:** a Literal holds `is_float`, not compared, so 0.5 and `Decimal("0.5")` are still one
  calculation. `trees.HIVE_FUNCTION_ARGUMENTS` holds the counts Hive and Spark both take.
- **Tests:** `tests/hive_literals.py` reads a Hive value back by its characters, so the three
  whole-Statement escaping tests are shared; `conftest.in_this_edition` names what a test
  expects where the Hive differs on purpose; `tests/spark_edition/test_spark_writing.py` breaks
  the escapes four ways and holds that `to_hive` refuses.

## Comments

**Plan change for ticket 18.** Ticket 18 asked to move the shared asserts that show a declared
row into per-edition files. They stay shared, with `in_this_edition(sql, spark)`, so both
Editions still run them.

**Code review (2026-09-29), `ec2b4ef`.**

- *Standards:*
  - **Fixed:**
    - "engine", an avoided word, left `readable`'s docstring (also D36).
    - The writer's docstring no longer restates `DECLARED_DIFFERENCES` with a pointer to a file
      that doesn't ship. It says what each difference looks like in plain words and that the
      README gives the reasons (ticket 26 generates that section from the rows).
    - The hive_function row says why the Editions differ.
    - `declared_differences_in` and its copy of `_nonzero_number` are gone. Ticket 18's parity
      test lists each row's cases instead.
    - The Literal part is `is_float`. `readable_text` uses a context variable, not a note on
      the tree, which `meta`'s contract rules out. `string` and `name` are private.
    - "takes 1 arguments" is gone; `_arguments` words the count.
  - **Answered, not changed:**
    - The layout helpers keep sqlglot's parameters (`dynamic`, `new_line`, `skip_first`,
      `skip_last`), so the port can be read against sqlglot line by line.
    - The reader's escapes, `_CONTROLS`, are kept apart from `_ESCAPES` on purpose: derived from
      them, a slip in one would read back as right.
    - The docstring's sqlglot version and `LAYOUT_MIRRORS_SQLGLOT` are ticket 18's.
- *Spec:*
  - **Fixed:**
    - "every literal and quoted name decodes to what was written": the reviewer's four breaks,
      a quote or backslash left bare, a doubled quote and a newline as a tab, passed `to_hive`.
      Each value and name is now checked as it is written, and a test breaks each.
    - `\a`, `\f` and `\v` are no longer escapes the writer writes or the reader accepts, since
      Hive and Spark read them as letters (finding 04). The Toolbox refuses those values first.
    - The commit message's "byte for byte ... except three declared differences" missed the 5
      cases that wait for ticket 25. The Answer above lists them, and ticket 18's parity test
      holds them.
  - **Answered, not changed:**
    - Until ticket 25, the Editions refuse different hive_function calls (for example length
      with 2 arguments). Ticket 25 makes SQL Composer count by the same list.
    - `readable_text` was judged justified.

**Drift review, `ec2b4ef`:** D35-D39, all closed by `baa3052`. D35 found that the new Literal
part made 0.5 and `Decimal("0.5")` different calculations in SQL Composer. It now isn't
compared, so 2.1's behaviour stands.

**Beginner reader:** [report](../reports/17-beginner-reader.md).

- **Changed:**
  - Stop 22 (the costliest): a refusal's call text, and so its opt-out, is built from the
    Python that made the calculation (`tables.python_text`), not its Hive. In Spark an opt-out
    no longer holds NULLIF or 0.5D and can be pasted back. It changes no case of SQL Composer's
    golden, and CHANGES says so.
  - Stops 1-16: the writer's docstring and the argument refusal are in plain words; what
    NULLIF and 0.5D are is said, and that the D isn't days. hive_function's docstring holds in
    both Editions. The HIVE_FUNCTION_ARGUMENTS comment says what the list does.
- **For later tickets:**
  - Stops 12, 17-21 (NULLIF and 0.5D have no public explanation) go to ticket 26's README
    section, generated from `DECLARED_DIFFERENCES`, which must say the D isn't days.
  - Stop 23 (no Worked example shows them): ticket 22 considers a ratio example.
- **Not changed:**
  - Stop 24: the lineage's "which is" is v2's wording, shared by both Editions.
  - Stop 25: the brackets are v2's.
  - Stops 18 and 19: shared docstrings can't say what only one Edition writes.
