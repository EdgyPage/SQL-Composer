# Ship both Editions as 3.0

Type: task
Status: ready-for-human
Blocked by: 23, 25

## Question

Export both folders to `main` together, as 3.0.

- `EXPORTED` becomes every Edition, with a test.
- `docs/clean-branch-readme.md` covers both Editions: which folder to copy and what each needs
  (each range sentence tested against its `engine.py` constants); one set of runnable examples,
  run as doctests in both runs, with the line "with Spark Composer, write `spark_composer`
  wherever this page writes `sql_composer`"; a block showing
  `send=lambda hive: spark.sql(hive).toPandas()`; the Spark settings the text relies on (ANSI,
  `escapedStringLiterals`, `enforceReservedKeywords`) and the ACID caution, for a one-time check
  by hand; a generated section on where the two Editions' Hive differs; a gallery paragraph per
  Edition; and "copy a whole folder".
- Raise TOOLBOX_VERSION to "3.0" in every `.py` of both folders, quoting the user's decision of
  2026-09-29 (ticket 01).
- A `## 3.0` section in `CHANGES.md`, copied verbatim to both folders.
- A line on Editions in `.claude/agents/beginner-reader.md`.
- Close the folded version items, then run the export once.

## Done when

- Both runs and all four CI jobs pass on the exported commit.
- The code review has run with this ticket as its spec, and no drift item is open.
- The beginner reader has read the README and the cheat sheet as a sqlglot user and as a Spark
  user, and its report is linked.
- `main` holds exactly `.github/README.md`, `sql_composer/*` and `spark_composer/*`, stamped
  "<product> 3.0, exported <same time>", as one commit on top of 955dafd.
- The user pushes `main`, copies `spark_composer/` at work, and runs the README's first
  Statement with `send=lambda hive: spark.sql(hive).toPandas()` on a table they already query.

## Comments

**From ticket 17 (2026-09-29).** The README section generated from `DECLARED_DIFFERENCES` is
the only public place that explains NULLIF and `0.5D` (beginner reader, stops 12 and 17-21).
Each row's why must be in plain words for a pandas user: NULLIF(y, 0) gives NULL where Spark
would stop the whole query; `0.5D` is an ordinary float (a DOUBLE), and the D doesn't mean
days. Spark Composer's `writing.py` docstring says the README gives the reasons.

## Answer

Both Editions ship as 3.0 (`efba5ab`, `4b56891`; reworked in `ecfce5c` after the review and the
two beginner readings):

- **EXPORTED** names SQL Composer and Spark Composer, so the export builds, checks and commits
  both folders; a test holds it. The preview gives exactly `.github/README.md`, `sql_composer/*`
  and `spark_composer/*`, each folder stamped "<product> 3.0, exported <one time>", each
  imported in a fresh Python with the other library blocked.
- **The README** covers both: which folder to copy and how to choose, what each needs with a
  pip line (held to each `engine.py`'s constants by a test), "write `spark_composer` wherever
  this page writes `sql_composer`", "copy a whole folder", one set of examples run as doctests
  in both runs (`tests/test_readme.py`), the Spark send, the date the examples take as today,
  the Spark setting to check by hand and the ACID caution, a paragraph on each gallery, where
  the two Editions' Hive differs (written by the export from `DECLARED_DIFFERENCES`, each row
  now with a title), and one cheat sheet. main's commit and the README's stamp name both
  Editions.
- **TOOLBOX_VERSION is "3.0"** in every `.py` of both folders, quoting the user's decision of
  2026-09-29 in `4b56891`'s message.
- **CHANGES.md** gains a 3.0 section, the same in both folders: the two Editions, ticket 25's
  Hive changes, the two mix-ups refused, and the fixes made since `main` was last exported as
  2.1 (955dafd), which were written under 2.1 for a re-export that never came. The 2.1 section
  is again what `main` shipped.
- **The beginner reader's brief** says the Toolbox comes in two Editions and which to read.
- **The version items** D76, D77, D79 and D82 are closed by the raise.

**Left to the user:** push `main` (`git push origin main`), copy `spark_composer/` at work, and
run the README's first Statement with `send=lambda hive: spark.sql(hive).toPandas()` on a table
you already query. The Status stays `ready-for-human` until then.

**Not done, and why:**

- **The cheat sheet's VERSION line** shows SQL Composer's value: the README is written for
  SQL Composer and says to write `spark_composer` for `sql_composer`, and the value says which
  Edition a copy is.
- **The version raise** is one line in each of 24 files, since each file carries
  TOOLBOX_VERSION so a mixed folder stops on import (the user's lockstep decision).

## Comments

**Code review (2026-09-30), `86140a7..4b56891`,** with the beginner reader as a SQL Composer
user and as a Spark Composer user, each finding checked by a second reader.

- **Fixed:**
  - `1dd6167`: CHANGES said "sqlglot still checks a function the list doesn't hold", which
    ships in Spark Composer too (also D91).
  - `ecfce5c`: the README's choice between Editions, the examples' today, SQL Composer's send,
    the pip lines, the Spark check and the ACID note, "except in", the update step, arithmetic
    beside the cheat sheet; the declared rows' wording (division under ANSI, the float's e, the
    hive_function row, and yyyy in a date_format pattern, now in hive_function's docstring
    too); CHANGES' three inexact lines; main's commit subject and the README's stamp naming
    both Editions, from one version_text; Spark Composer's writing.py pointing to the README;
    the brief's Java; and the tests (each Edition's files below their stamps, one differences
    line pinned as text, the README's Python and pip lines against the constants).
- **Answered, not changed:** the items above under Not done; and the cheat-sheet first lines
  both readers stopped on (write_table_reference, contains, average_of and others), which
  predate this ticket and read the same in both Editions: the follow-ups below rework them.

**Drift reviews.**

| Items | Opened by | Closed by |
|---|---|---|
| D76, D77, D79, D82 (version) | ticket 25 | `4b56891` |
| D90 | `efba5ab` | `4b56891` |
| D91 | `4b56891` | `1dd6167` |
| D92 | `ecfce5c` | `d1dbe31` |
**Beginner reader:** read at `4b56891` as a [SQL Composer
user](../reports/26-beginner-reader-sql.md) and as a [Spark Composer
user](../reports/26-beginner-reader-spark.md).

- **Changed:**
  - SQL user's costliest stop, a pasted example giving no rows: the README says the examples
    take today as 2026-09-25, and what to write instead.
  - The date_format 'YYYY-MM' stop: write yyyy, in the README and in hive_function's docstring.
  - Choosing by query API against by engine: the README says each difference is for Spark.
  - Spark user's costliest stop, ACID with no fix: the note says what an ACID table is and
    what to ask for.
  - The hive_function row that spoke of a list the README never introduced: rewritten.
  - Dividing never shown: the cheat sheet's introduction says how.
  - The settings to check: one to check, with what to do, and two that may be either.
  - Java 17 to 21 and "apart from yours": a second Python, leaving `spark` alone.
  - SQL Composer's send with no example; the two versions with no pip line.
  - "but in", the update step, "the docstrings' examples and the Worked examples", and the
    three CHANGES lines.
- **Answered, not changed:** the cheat-sheet first lines, as above; the Example database's
  made-up tables at work, which the README now answers by pointing to write_table_reference.

## Follow-ups, and 3.1

The user pushed main as 3.0 (`dcb698f`), then asked for the two follow-ups this record left
open, before main is re-exported. Since 3.0 was already pushed, they ship as 3.1, which the user
chose on 2026-09-30 when asked which version the re-export should carry (D93).

- **A struct column at sqlglot 25.24.2** (`426e4ea`, `7355bfb`). sqlglot 25.24.2 writes
  STRUCT<name STRING>, without the colons Hive's grammar needs, and drops them again when
  to_hive reads its own Hive back, so writing them can't work there. SQL Composer refuses a
  struct column where its sqlglot writes none, found by writing one, and says which sqlglot to
  install; `check_writable_type` joins the Editions' interface beside `check_writable_call`,
  and Spark Composer's refuses nothing. The README says a struct column needs sqlglot 30.19.0
  or newer.
- **The cheat-sheet first lines** both beginner readers stopped on (`426e4ea`, reworked in
  `7355bfb` after the review and two new readings found some rewordings made new stops):
  write_table_reference, contains, starts_with, average_of, Table, check_key, create_table,
  AS, FROM, JOIN, ORDER_BY, row_number, hive_function, by_day and refusals.py. contains'
  docstring says why LIKE needs your % and _ escaped, with an example; hive_function's says
  only one Edition renames a call.
- **3.1** (`7d66dd6`): TOOLBOX_VERSION in every .py of both folders; CHANGES' 3.1 section with the
  two follow-ups' lines, its 3.0 section again what main shipped.

**Code review (2026-09-30), `426e4ea`,** with the beginner reader as both kinds of user
([SQL Composer](../reports/26-followups-beginner-reader-sql.md),
[Spark Composer](../reports/26-followups-beginner-reader-spark.md)), each finding checked by a
second reader. Fixed in `7355bfb`: average_of's line, which read as the average function
refusing itself; "taken as typed", where "typed" means a data type elsewhere; AS's "name a
table"; JOIN's self-definition; hive_function's "your values"; by_day's "per day it reads";
the stops left (Table and check_key's key, ORDER_BY's LIMIT, row_number's group, where a
Warning shows); hive_function's docstring; first_look and the struct in the README; and the
struct check's substring test, retyped install advice and parameter name. Answered, not
changed: the type refusal's struct example, which a sqlglot below 30.19.0 then refuses, is
followed by a refusal that says what to install; `hive_function("struct", ...)` and
`named_struct`, which predate these follow-ups, are left for a ticket of their own; the CHANGES
lines the readers stopped on under 3.0 are as 3.0 shipped them.

| Items | Opened by | Closed by |
|---|---|---|
| D93 (version) | `426e4ea` | `7d66dd6` |
| D94, D95 | `7355bfb` | `7d66dd6` |

**Left to the user:** push main again, now 3.1, and try spark_composer at work as above.

