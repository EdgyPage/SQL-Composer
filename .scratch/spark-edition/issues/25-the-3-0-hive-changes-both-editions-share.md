# The 3.0 Hive changes both Editions share

Type: task
Status: resolved
Blocked by: 04, 21, 23, 24

Findings: [ticket 04](../findings/04-spark-reads-the-hive.md) gives the evidence and wording
this ticket uses.

## Question

The user approved these changes to SQL Composer's own Hive (2026-09-29), so both Editions write
the same text. Each changes the shared tree or a shared list, so both printers follow. One commit
each, with ticket 4's evidence cited:

- **`CAST(... AS STRING)` around week_start and month_start.** Spark's NEXT_DAY and TRUNC return
  DATE while the Toolbox types both results as string; Hive's results don't change.
- **Backticks for Spark's reserved words** (such as ANTI, SEMI, MINUS, EXCEPT, NATURAL, SETMINUS,
  as ticket 4 lists them), in column and table names, DESCRIBE and SHOW PARTITIONS included.
- **Strict create_table types:** only types on an explicit Hive list, in `trees.py`, instead of
  whatever sqlglot's `DataType.build` accepts.
- **The shared hive_function argument and aggregate list in SQL Composer too**, so the same
  Guards fire in both Editions. SQL Composer's answer changes for names such as lag, first and
  count_if.
  Window functions (lag, lead, rank, ...) are refused through `hive_function`, which can't
  write OVER.

Each commit regenerates both goldens and both galleries, updates the doctests, and removes the
strict xfails that waited for it. The drift reviewer opens a `version` item for each; answer it
"folds into 3.0" and leave it open until ticket 26. Open items freeze exports, so run tickets 25
and 26 back to back.

## Done when

The Definition of done in `CLAUDE.md` holds, except the open version items this ticket lists for
26; both runs and all four CI jobs are green with no strict xfail left; the parity test passes
with only the division, hive_function and float-literal rows.

## Comments

**From ticket 17 (2026-09-29).**

- Spark Composer already counts hive_function's arguments by `trees.HIVE_FUNCTION_ARGUMENTS`;
  SQL Composer checks through sqlglot. Until this ticket they refuse different calls, such as
  length with 2 arguments or regexp_replace with 1. SQL Composer's refusal also reads "was
  given 1 arguments"; Spark Composer's `_arguments` words the count, and SQL Composer should
  share it.
- Two rows of `DECLARED_DIFFERENCES` wait for this ticket, `create_table_types` (4 cases) and
  `hive_function_arguments` (1). The parity test holds that each listed case still differs, so
  this ticket takes the rows out once SQL Composer checks the same way.
- `hive_function("date_format", dt, "YYYY-MM")`: SQL Composer writes 'yyyy-MM' (sqlglot's
  rewrite), Spark Composer 'YYYY-MM' as given, and YYYY is the year a week belongs to, which
  Spark 3 and later refuse in a pattern. The shared list could refuse or warn on it.

## Answer

The four changes the user approved on 2026-09-29, one commit each, each with ticket 04's
evidence in its message, and both goldens and both galleries regenerated:

- **`CAST(... AS STRING)` around week_start and month_start** (`2029bff`). Spark's NEXT_DAY and
  TRUNC give a date; the CAST makes the week and month text on Spark, as Hive gives it. A
  `Cast` kind joins the tree. SQL Composer's Example database hands sqlglot's executor a plain
  CAST where the CAST is to text, so its message still names NEXT_DAY or TRUNC.
- **Backticks for the words Spark reserves** (`3e85a8b`). HIVE_RESERVED gains ticket 04's 28
  words, and the golden corpus a table, `ops.semi`, named and columned with them.
- **Strict create_table types** (`e6d8ea8`, `5c5dc9d`). HIVE_TYPES and is_hive_type in
  trees.py: the types both have, spelled as DESCRIBE prints them, decimal, varchar and char with
  their sizes up to what both take, a map keyed by a single value, a struct's names plain words.
  The refusal says what to write for a type people often use, such as integer.
- **One hive_function list in both Editions** (`9ba0f91`, `e9b0de0`, `01416d6`). In trees.py:
  HIVE_FUNCTION_ARGUMENTS counts 111 functions' arguments, HIVE_AGGREGATES is every aggregate
  Spark's own registry lists at 3.5.0 and 4.0.4, and Hive's, and WINDOW_FUNCTIONS, the 9 it
  refuses since it can't write OVER, with the pandas to use instead. The checks are in the shared
  calculations.py; the Editions' interface trades function_adds_rows_up for
  check_writable_call, where SQL Composer's sqlglot still checks a function the list doesn't
  hold. The Spark acceptance tests hold the lists to Spark's registry at both versions.
- **Done when:** `DECLARED_DIFFERENCES` holds division, float and hive_function, and no strict
  xfail is left: the four that waited for this ticket pass.

**Not done, and why:**

- **The version items stay open** (D76, D77, D79, D82), answered "folds into 3.0", as this
  ticket says: ticket 26 raises TOOLBOX_VERSION.
- **SETMINUS isn't in the list,** though the Question names it: it is Spark's lexer's name for
  MINUS, which is, and `SELECT 1 AS setminus` parses in every mode (the review checked).
- **date_format's 'YYYY-MM'** (ticket 17's Comment) is neither refused nor warned of: it isn't
  among the four approved changes, and the hive_function row declares that SQL Composer writes
  'yyyy-MM' where Spark Composer writes it as given.
- **A struct at sqlglot 25.24.2** is written without its colons, which Hive's grammar needs. It
  was so before this ticket, and a separate task is flagged for it.
- **percentile_cont, percentile_disc, grouping and grouping_id** are aggregates Spark lists, but
  need WITHIN GROUP or GROUPING SETS, which the Toolbox doesn't write; Spark refuses them with
  its own message when the Statement runs.

## Comments

**Code review (2026-09-30), `1cc5f34..9ba0f91`,** with the beginner reader, each finding checked
by a second reader.

- **Fixed:**
  - `e9b0de0`: min and max had no count, so max with 2 arguments, which sqlglot writes
    GREATEST, counted as an aggregate and the GROUP_BY Guard let wrong Hive through; the list
    now counts 111 functions. sqlglot's KeyError, IndexError and UnsupportedError no longer
    leak. SQL Composer's remaining sqlglot refusal reads plainly ("gives nvl2 1 argument, and
    sqlglot can't write nvl2 with it"), with the shared count words. hive_function's docstring
    names Hive functions and says what each check changes; the window refusal names the pandas.
    check_call is check_writable_call.
  - `5c5dc9d`: decimal alone and decimal(p), which check_table_reference then flagged, are
    refused, and so are sizes neither engine takes, maps keyed by a collection and structs with
    reserved names, which SQL Composer wrote as a bare STRUCT.
  - `5bf68d8`: week_start's and month_start's docstrings, backticks in Table's, the Example
    database's CAST, and the lines made too long.
  - The declared hive_function row says SQL Composer refuses some calls sqlglot can't build
    that Spark Composer writes (`0c741a8`).
- **Answered, not changed:**
  - Spark Composer's check_writable_call refuses nothing: the interface needs it in both
    Editions, and only SQL Composer has a library that can't build some calls.
  - The type grammar is read in trees.py and again in Spark Composer's printer, which must lay
    each type out; the printer's own check can't fire once trees.py has.
  - The items above under Not done.

**Drift reviews.**

| Items | Opened by | Closed by |
|---|---|---|
| D76 (version) | `2029bff` | open until ticket 26 |
| D77 (version) | `3e85a8b` | open until ticket 26 |
| D78 | `3e85a8b` | `3ff89e9` |
| D79 (version) | `e6d8ea8` | open until ticket 26 |
| D80, D81 | `e6d8ea8` | `c7c496e` |
| D82 (version) | `9ba0f91` | open until ticket 26 |
| D83, D84 | `9ba0f91` | `c1c0a51` |
| D85 | `c1c0a51` | `3155870` |
| D86 | `e9b0de0` | `01416d6` |
| D87 | `01416d6` | `0c741a8` |
| D88, D89 | `5c5dc9d` | `5bf68d8` |

**Beginner reader:** [report](../reports/25-beginner-reader.md), read at `9ba0f91`.

- **Changed:**
  - The costliest stop, "add rows up, as first and count_if do": hive_function's docstring now
    says "turns many rows into one", names collect_set and percentile, which Hive has, and
    says what that changes (a name with AS, and GROUP_BY).
  - create_table's refusal for integer: it says to write int, why (spelled as DESCRIBE prints
    it), that the sizes are examples, and the struct, map and size rules.
  - Backticks: Table's docstring says you never type them, and where the Hive puts them.
  - The window refusal names the pandas for lag, lead, rank and dense_rank, and row_number(...)
    for row_number; "window" is explained where it is first used.
  - The sqlglot refusal reads like the count refusal, with the same count words.
  - "after its name" reads 'after "length"'.
  - week_start and month_start say "whether your warehouse runs the query on Hive or on Spark".
- **Answered, not changed:**
  - SQL Composer's Example database can't run week_start or month_start: its refusal says so,
    naming NEXT_DAY or TRUNC, and the gallery shows pandas' result instead.
  - Table takes "integer" where create_table doesn't: Table checks a value's kind against a
    type, which integer names well enough; create_table needs the type DESCRIBE prints.
  - count_if given a condition: hive_function takes columns and values, not conditions;
    count_rows(where=...) counts rows where a condition holds.
