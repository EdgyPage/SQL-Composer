# Aggregate and window placement from the tree

Type: task
Status: claimed
Blocked by: 02

## Question

A Column carries two flags, `_aggregate` and `_window`, copied by hand into it at about eight
places in `calculations.py` and `tables.py`, though the tree already says whether it adds rows
up or numbers them. One flag is computed wrongly and the other is never read, so Hive the
Warehouse rejects gets past `statement(...)` (candidate 3 of [report.html](../report.html)):

1. **The GROUP BY Guard misses outputs Hive rejects** (`clauses.py` `_guard_group_by`):
   - a column inside a grouped calculation counts as grouped;
   - an output that mixes an aggregate with a plain column, such as
     `job_runs.duration_mins - max_of(job_runs.duration_mins)`, is skipped whole;
   - HAVING and ORDER_BY are never checked.
2. **Aggregates are refused only in WHERE**; in ON= or GROUP_BY they reach the Warehouse.
3. **row_number is never refused where Hive refuses it**: in WHERE, HAVING, ON=, GROUP_BY, or
   inside an aggregate. `Column._window` is computed for this and never read.
4. **fill_null takes its aggregate flag from its first argument only**, so
   `fill_null(job_runs.status, max_of(...))` skips the GROUP BY Guard.
5. **ORDER_BY's output names are never checked**, where GROUP_BY's are, so a typo reaches the
   Warehouse (and leaks a raw sqlglot error on SQL Composer's Example database).
6. **row_number's lists**: `ORDER_BY=[]` leaks a raw sqlglot ParseError, and a string sort key
   inside OVER is written as a bare name, which can never be an output of the same SELECT.
7. **GROUP_BY() with nothing** is the one clause that takes nothing, and is silently dropped.

## Decisions (the user asked for this candidate on 2026-10-03; the rest are the agent's)

- **The tree is the one source.** `Column._aggregate` and `Column._window` are read from the
  tree, and the `aggregate=` and `window=` arguments go, with every place that passes them.
  That fixes item 4 by construction.
- **One placement check** at `statement(...)`: an aggregate is refused in WHERE, ON= and
  GROUP_BY; a row_number in WHERE, HAVING, ON= and GROUP_BY. Each fix says where it goes
  instead: HAVING for an aggregate, a `derived(...)` table for a row_number. An aggregate or a
  row_number inside an aggregate is refused when the calculation is made.
- **The GROUP BY Guard walks the tree** of each output, HAVING condition and ORDER_BY key: a
  part equal to a GROUP_BY column or calculation is grouped, an aggregate is fine whatever is
  inside it, and any other column is missing. An ORDER_BY key that names an output is fine.
- **ORDER_BY's names are checked** against SELECT's output names, in GROUP_BY's words.
  row_number's ORDER_BY takes only columns or `descending(column)`, and both its lists need at
  least one item; descending's docstring says names work only in ORDER_BY(...).
- **GROUP_BY() refuses nothing to group by**, in ORDER_BY's words.
- **Out of scope:** `sort_array`'s argument count, which needs Hive's own source checked first.

## Done when

- Each of 1-7 has a test through the public names, run in both Editions; every new refusal is
  four-part.
- Both runs pass; goldens and galleries regenerated if their text changed.
- The code-review skill has run with this ticket as its spec, the drift items are closed, and
  the beginner reader has read the new refusal text.
