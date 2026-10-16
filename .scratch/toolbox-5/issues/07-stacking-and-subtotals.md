# Stacking and subtotals

Type: task
Status: resolved
Blocked by: 01
Size: M

## Question

Map family 7. UNION_ALL, UNION, INTERSECT, EXCEPT over whole Statements, matched by output
name, a mismatch refused naming the column; Lineage feeds each output from every branch.
GROUP_BY(rollup(...)), cube(...), grouping_sets(...), with is_total(column); a Saved table
written from a rollup refused.

## Done when

- Each in both Editions, with a how-to for reconciling two tables and one for subtotals.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).

## Answer

Built on branch `worktree-agent-af1a5baa3f9895606` in `a1ee296`, then reworked after the code
review and the beginner reader in the commit that resolves this ticket.

**What was built**

- **A new core file, `composer_core/stacking.py`** (in `tools/editions.py`'s `CORE_FILES`),
  with eight public names, all decided by this ticket: `UNION_ALL`, `UNION`, `INTERSECT`,
  `EXCEPT`, `rollup`, `cube`, `grouping_sets` and `is_total`. Public names go from 67 to 75.
- **Stacks.** `UNION_ALL(*statements, returns_all_rows=False)` and the other three take two or
  more Statements (or a list) and return a Statement whose `_stack` is (call, Statements).
  Columns are matched by name: each Statement's SELECT is written in the first one's order.
  Refused, each naming its Statement (1st, 2nd, ...) and column: a Statement that lacks a
  column or returns an extra one (with the `AS` that renames it when one of each), a column
  whose type is a number in one and text in another (type families, compared with the first
  Statement that knows the type), a Derived table, a write, a Stack inside a Stack (Hive takes
  no brackets there; the fix names it with derived), a Statement with ORDER_BY or LIMIT, two
  different Derived tables of one name, fewer than two Statements. A Stack is a Statement
  everywhere: to_hive (one WITH at its top for every Statement's Derived tables, the automatic
  LIMIT once at the end), run, show_hive, derived(...), JOIN on a derived Stack, the dates cap
  (each Statement's days), writes reading a derived Stack (each Statement's bottom must read
  the same one day, refused naming each table's days otherwise), by_day (each Statement split
  to the day; a UNION, INTERSECT or EXCEPT only when each Statement returns the day under one
  name, else the new Guard `guard_by_day_stack`), and export_lineage.
- **Keys** (`keys.py`): UNION, INTERSECT and EXCEPT give each different row once, so every
  column is a Key (the day held to one value for a write); EXCEPT also keeps the first
  Statement's Keys and INTERSECT every Statement's; UNION_ALL has none ("UNION_ALL(...) keeps
  every row of each of its 2 Statements, and rows of two of them may share a Key"), so its
  write is refused by the Key check unless `unproven_key=True`. Subtotals have none.
- **Subtotals.** `rollup(...)`, `cube(...)` and `grouping_sets(...)` make a `Subtotals` object
  that `GROUP_BY` takes beside plain columns (the plain ones are in every set; one Subtotals
  per GROUP_BY; output names such as "week" work). Both Editions write
  `GROUP BY a, b GROUPING SETS ((a, b), a, ())`, the form Hive (0.10+) and Spark both take,
  rather than `ROLLUP(...)`/`WITH ROLLUP`; a one-column set is written bare, as sqlglot reads
  `(a)` back as a bracketed column. sqlglot 25.24.2 writes a comma before GROUPING SETS, which
  Hive refuses, so `sql_text` now makes sqlglot's generator itself with that separator empty
  (the one-function test now allows `generator`/`generate` in `sql_text` only).
  `is_total(column)` is the condition `GROUPING(column) = 1` (Hive 2.3+, Spark); GROUPING
  counts as an aggregate (`trees.AGGREGATES`), so it goes where a count goes. Refused: is_total
  in WHERE, ON= or GROUP_BY; in a Statement with no subtotals; of a column GROUP_BY doesn't
  group by; in HAVING or ORDER_BY of a column SELECT doesn't return (Spark refuses it, checked
  on the Spark Example database); alone in SELECT (the fix shows the `if_else` form). A write
  whose rows come from subtotals at any step (the Statement, a Derived table, a Stack's
  Statement) is refused, not a Guard, so with no opt-out. by_day keeps subtotals only when the
  day is in every set, its fix saying to move the day out of the subtotals to a plain column.
- **The Example databases.** sqlglot's executor silently ignores GROUPING SETS (it gave no
  subtotal rows), so sqlglot Composer's `run_query` refuses them with "its executor has no
  GROUPING SETS"; it runs the four Stacks. Spark Composer's runs both. No table was added:
  how-to 33 reconciles `ops.jobs` (each job's team today) with `ops.job_owners` (each day's
  team), which disagree on 2026-09-17 about report_build and agree on 2026-09-24.
- **Lineage.** Each Statement of a Stack is drawn as a step of its own, "<name>, 1st
  Statement", ...; a UNION_ALL or UNION column is fed from that column of every Statement; an
  INTERSECT or EXCEPT column from the first Statement's, the others' columns feeding a
  condition box, "EXCEPT in <name>", that decides its rows (a decision of this ticket: their
  values come from the first Statement). Each Stack's and subtotals' Keys line says what it
  keeps or loses. A write reading a Stack draws "day written" from every Statement's bound.
- **Docs and tests.** Docstrings with Worked examples for each name (gallery entries); how-to
  33 "Reconcile two tables" and 34 "Subtotals and grand totals" (with pandas stand-ins for
  sqlglot Composer; Intermediate is now 19 to 34, in `tools/how_to_page.py`,
  `tests/test_how_tos.py` and `tests/repo/test_export_clean.py`); CHANGES 5.0 "New" lines;
  CONTEXT words **Stack** and **Subtotal row**; `tests/test_stacking.py` (both Editions:
  Hive, refusals, Keys, writes, by_day, Example database results, Lineage), a refusal test
  for `guard_by_day_stack`, golden corpus cases `edge:stack:*` and `edge:subtotals:*` (a wide
  set wraps the same in both Editions), and a CI-only case writing a UNION into a real Spark
  Hive table (`test_spark_hive_tables.py`, NEEDS_WINUTILS: not run here).

**Code review** (code-review skill, since 5b82ba1). Spec: fixed is_total in ORDER_BY, which
was never checked (now checked as anywhere else, and refused for a column SELECT leaves out,
which Spark refuses too); fixed by_day's fix for a day inside the subtotals; fixed the type
check to compare with the first Statement that knows a type, not only the first. Lineage of
INTERSECT/EXCEPT from the first Statement only: kept, as above, and CHANGES now says so.
Scope beyond the list (by_day of Stacks, writes from Stacks, the sqlglot separator) follows
from "a Stack is a Statement" and Hive's grammar: kept. Standards: "level" (a glossary word)
removed from docstrings, how-to 34 and its stand-in; "stacking" as a noun in the writers'
comments reworded; Spark as the reason for the HAVING refusal reworded for a sqlglot Composer
user; CHANGES' untrue Lineage sentence and `_add_stack`'s docstring fixed; `grouped()` now
returns the subtotals' text instead of setting it on the Statement; stray blank lines removed.
Kept, as judgement calls: `_stack` as a (call, Statements) pair, like the Statement's other
plain attributes; the kind of Stack told apart by name in a few places (a table of facts per
kind would be the machinery the standards prefer to avoid for four names); the Stack checks
spread over the functions that walk Statements (a Stack is a Statement, as the standards'
"no class hierarchy" asks); `clauses.derived_tables` repeating `stack_steps` inline and
clauses importing stacking inside functions (clauses.py is the shared hotspot; stacking.py
imports it, as keys.py does).

**Beginner reader:** [report](../reports/07-beginner-reader.md), 35 stops (2 stuck). Done:
rollup's and is_total's first lines say what rows you get and what is_total tests; "adds up"
for a column is now "totals over" everywhere (docstrings, refusals, CONTEXT, how-to 34);
GROUPING SETS's lines and `()` are named in rollup's docstring, which also says sqlglot
Composer's Example database can't make subtotals; UNION_ALL's position-vs-name sentence split,
"a number in one Statement and text in another", the Key and the LIMIT that
set_load_limits adds said plainly; UNION's and INTERSECT/EXCEPT's Key sentences moved to a
paragraph saying what they buy; EXCEPT's example says what it gives; "beside" replaced by "as
well" / "added to the groups' rows"; the Toolbox, not Hive, refuses writing subtotals;
cube's count renamed job_count; "[] is the grand total"; the HAVING/ORDER_BY refusal's why;
guard_by_day_stack's what and fix; the different-days and Derived-table-name whys; CONTEXT's
Stack names its four functions; CHANGES' grammar and by_day's limit; how-to 33's counting and
Key lines; how-to 34's sort note, rollup "drops its columns from the right", the NULL/None
note and the "Week and month rollups" link. Left: `job_runs` undefined in the docstrings'
examples (the doctests' convention, as everywhere); ORDER_BY without LIMIT in a Stack's
Statement meets its Load limit first (existing order of checks).

**Open questions for the user**

- Hive at work wasn't available: GROUPING SETS with an expression (a named calculation such as
  `rollup("week")`) and `GROUPING(col)` in HAVING are written as Hive 2.3+ documents them, and
  were run on Spark only. The refusal of is_total in HAVING or ORDER_BY of a column SELECT
  leaves out is Spark's rule, applied to both Editions; Hive may not need it.
- The Example database gained no table: reconciling uses `ops.jobs` against `ops.job_owners`.
  Ticket 05 may add a table for FULL_JOIN; how-to 33 could switch to it if it suits better.
