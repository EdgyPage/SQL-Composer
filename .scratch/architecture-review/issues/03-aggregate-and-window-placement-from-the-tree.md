# Aggregate and window placement from the tree

Type: task
Status: resolved
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
  row_number's ORDER_BY takes only columns or `descending(column)`, and at least one;
  descending's docstring says names work only in ORDER_BY(...). An empty PARTITION_BY stays
  allowed: it numbers every row, and both Editions write it the same, `OVER (ORDER BY ...)`.
- **GROUP_BY() refuses nothing to group by**, in ORDER_BY's words.
- **Out of scope:** `sort_array`'s argument count, which needs Hive's own source checked first.

## Done when

- Each of 1-7 has a test through the public names, run in both Editions; every new refusal is
  four-part.
- Both runs pass; goldens and galleries regenerated if their text changed.
- The code-review skill has run with this ticket as its spec, the drift items are closed, and
  the beginner reader has read the new refusal text.

## Answer

Built in `81782bd` (with drift item D106 from `8a13bda`), reworked after the review in `2699ea9`.

- `Column._aggregate` is read from the tree (`has_aggregate`); `trees.py` gains `is_aggregate`
  and `has_window`. The `aggregate=` and `window=` arguments are gone, and so is
  `Column._window`, which nothing read once the checks read the tree.
- `_check_placement` refuses a count or a sum in WHERE, ON= and GROUP_BY, and a row number in
  WHERE, HAVING, ON= and GROUP_BY; GROUP_BY's fix says to group by a Derived table's column.
  `_not_inside` refuses a count, a sum or a row number inside `sum_of` and its siblings, their
  `where=`, and an aggregate `hive_function` such as collect_set.
- The GROUP BY Guard walks every output, HAVING condition and ORDER_BY key, and runs when a
  count is only in ORDER_BY too. Its refusal names the clause, and with no GROUP_BY at all
  says "but the Statement counts or adds up rows and has no GROUP_BY".
- `_check_order_names` checks ORDER_BY's names; row_number's ORDER_BY= takes only columns, at
  least one; GROUP_BY() refuses nothing to group by.
- `tests/test_placement.py` pins items 1-7 in both Editions.

**Beginner reader** ([report](../reports/03-beginner-reader.md)): 9 stops, all answered.

**Code review (2026-10-03), `81782bd`.**
- *Standards:* no hard violations. Fixed: `_not_inside`'s words ("total" no longer stands for
  every count), the no-GROUP_BY wording for HAVING and ORDER_BY, the ORDER_BY name check moved
  out of `_check_tables`, and by_day's `lost_in` list in place of an unlabelled pair. Kept:
  each place's fix as a branch where it is raised, which is plainer than a map of texts.
- *Spec:* an aggregate hive_function wasn't checked for a total inside it; an aggregate only in
  ORDER_BY skipped the GROUP BY Guard; a row number in ON= and GROUP_BY had no test; the
  no-GROUP_BY wording blamed SELECT for a count in HAVING. All fixed, with tests. An empty
  PARTITION_BY stays allowed (the ticket's decision is corrected): both Editions write
  `OVER (ORDER BY ...)`, pinned by a test. Left out, as before this ticket: a count inside a
  row number's ORDER_BY= with no GROUP_BY.

| Items | Opened by | Closed by |
|---|---|---|
| D106 | `8a13bda` | `81782bd` |
| D107 | `81782bd` | `2699ea9` |
