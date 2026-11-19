# Hive that stays small: the docs and Copilot files swept for bloated CTEs

Type: task
Status: resolved
Blocked by: 05, 06
Size: L

## Question

The user (2026-11-19): "add a ticket that sweeps the documentation to make sure the sql produced
is memory efficient. I just wasted an hour of time 'debugging' an inefficient statement that has
no logical errors in it, just was written to have bloated ctes."

What the docs, the Copilot files and the Hive the Toolbox writes teach about a CTE's cost, so
the SQL a person or Copilot writes from them stays small in Hive: right rows, and no more work
than the rows need.

## Done when

- **The rules, written once and checked against Hive's own documentation** (the `research`
  skill, primary sources only), each with why, in a short section every Copilot file loads
  (`tools/copilot_sources/_always.txt` or a file of its own, within the 9,000 limit) and in the
  docs where a person writes Hive (the how-tos on joins, windows and converting). The ones to
  check and keep or drop:
  - **A CTE read more than once is worked out each time it is read.** Hive keeps no CTE's rows
    unless `hive.optimize.cte.materialize.threshold` says so (check the default and the version
    the user's warehouse runs). Read it once, or make it a Staging table or a Saved table.
  - **A CTE carries only the columns something after it reads**: no `SELECT *` in a CTE, no
    column carried "in case".
  - **Filter and group before joining**: the WHERE (a Partition's first) in the CTE that reads
    the big table, an aggregate before the join it feeds where the rows allow.
  - **A chain of CTEs that each copy the whole table to rename or add a column** is one SELECT.
  - **No ORDER BY in a CTE or subquery** without a LIMIT (file 12's S3 already says it of M);
    **no DISTINCT to undo a join's fan-out**: fix the join.
- **The sweep**: every SQL block and every Hive a Statement writes in `docs/` (how-tos, Worked
  examples, the Example gallery, the Workflows overview), the README, Copilot files 00 to 21,
  `worked_examples/`, and the Example projects. Each break fixed, or named in this ticket with
  why it stays.
- **The Excel path, both ways**: file 15 writes each step as a CTE "in each final reading it".
  Within one final, a step read twice (a Total Row's or a pivot's total level reading the
  Table's own final, a step two others read) is worked out twice; and a step's CTE carries every
  column of its Table, read or not. The code (tickets 04 to 06) and files 11, 12, 15 and 20
  follow the same rules, so the two paths stay equal (ADR 0016); what changes in a Copilot file
  is a change ticket 13 ties and ticket 14 scores.
- **A test holds it**: a repo test reads, with sqlglot, every SQL block in `docs/` and
  `copilot/`, the Hive each Worked example writes, and the Hive the Excel conversion writes for
  the evaluation's tasks, and fails on a CTE read more than once, a `SELECT *` in a CTE, a CTE
  column nothing reads, and an ORDER BY with no LIMIT in a CTE or subquery, each naming the file
  and the block. A break that must stay is listed in the test with its reason.
- The beginner reader runs on what changes in the how-tos, and its report is linked here.

## Out of scope (the user, 2026-11-19)

- **No Toolbox Warning on a Derived table read more than once**: "we can fix and tweak
  statements when the performance is in the way." This ticket teaches lean Hive; it adds no
  Toolbox behaviour.
- **No Staging table for a step several finals read**: each final keeps its steps as CTEs, as
  file 15 says.

## Answer

### The rules, checked against Hive's documentation (read 2026-11-19)

Each kept; where a rule's cost is not Hive's work alone, it says so.

| Rule | Kept, and why | Source |
|---|---|---|
| A CTE read more than once is worked out each time | Kept. `hive.optimize.cte.materialize.threshold` is -1, off, in 2.x, 3.1.3 and 4.0.0 (4.0's note: off "due to HIVE-24167"; HIVE-27856); in 4.1.0 it is 3, with `hive.optimize.cte.materialize.full.aggregate.only` true, so only a CTE with aggregate output read more than 3 times is kept: a CTE read 2 or 3 times is worked out each time on every release. The user's version isn't known (`clauses.py` names Hive 2.3 or 3.1 under Tez and asks whoever looks after the warehouse); on either, -1. The LanguageManual's CTE page says nothing of materialization. | HiveConf.java at `rel/release-3.1.3`, `rel/release-4.0.0`, `rel/release-4.1.0` (github.com/apache/hive); HIVE-27856 (issues.apache.org); hive.apache.org/docs/latest/language/common-table-expression |
| A CTE carries only the columns read after it; no `SELECT *` | Kept, its cost said plainly: the column pruner is always on (`hive.optimize.cp` removed in 0.13, HIVE-4113), so a column only carried is dropped where Hive works the CTE out in place; a column the CTE groups by never is (a row per value); every column is written where Hive materializes it (4.1); and a short CTE is the one a person debugs, the user's hour. | Configuration Properties, `hive.optimize.cp` |
| Filter (a Partition first) and group before joining | Kept. A map join needs the small side under `hive.auto.convert.join.noconditionaltask.size`, 10 MB; else Hive sorts both sides and buffers every table but the last on the reducers; aggregates are not pushed below a join (`hive.transpose.aggr.join`, false). `hive.optimize.ppd` (true) pushes a WHERE down, but a WHERE on a LEFT JOIN's right side makes it inner (the Joins page's ds example). | LanguageManual Joins; HiveConf 3.1.3 (map join size, `hive.auto.convert.join`); HiveConf master (`hive.transpose.aggr.join`) |
| A chain of CTEs each copying the table to rename or add a column is one SELECT | Kept, as a reading rule: inlined, the copies cost Hive little; each is one more step to debug, and is worked out again where read twice. No Hive doc. | - |
| No ORDER BY in a CTE or subquery without a LIMIT | Kept. ORDER BY's total order goes through one reducer; from 3.0 `hive.remove.orderby.in.subquery` (true, HIVE-6348) drops one with no LIMIT in a subquery or view, so it sorts nothing anyway; strict mode wants a LIMIT on any ORDER BY. | LanguageManual SortBy; Configuration Properties |
| No DISTINCT to undo a join's fan-out | Kept, as reasoning: the join makes every repeated row, then DISTINCT shuffles them all to drop the copies. | - |

Written once, short, with why:

- **Copilot files 01 to 10**: rule A11 in `tools/copilot_sources/_always.txt` ("Hive works a
  Derived table out at each read: read it once, SELECT in it only what is read after it, and
  filter and group in it before a join. Fix a join that repeats rows; no SELECT_DISTINCT after
  it."). A6 already holds ORDER_BY's LIMIT. To fit 9,000: A3 lost "comparisons are A4's"; file
  03 its Load line's last words, a shorter `t` term and `at_least` from its names (A4 still
  names it); file 05 a shorter Objective, Load line, R1, R2, R6, R7 and C4; file 09's "A1 to
  A10" is "A1 to A11".
- **Files 11, 12 and 15**, loaded together, which write Hive: rules H1 to H5 and self-check
  C10 in file 15 (`## Rules: Hive that stays small`). Files 00, 13, 14, 16 to 19 write no
  Statement or Hive of their own to sweep.
- **How-tos**: Keep reads and joins fast's new step 4, "Keep each step small": a worked example
  (`events_per_job` grouped before its join) and the six rules with their reasons; a pointer in
  Count, join and stay safe (joins, step 10), Look across rows (windows, step 8), Convert
  someone else's Hive (step 13: a Conversion keeps each script's shape; make it lean once it
  passes) and Share Building blocks (step 2).

### The sweep

Read by the new test (below), every block. Breaks found and fixed:

| Where | Break | Fix |
|---|---|---|
| How-to 05, step 2 | `job_totals` carried `runs`, unread | carries job_id and minutes |
| Gallery, `statements/step_by_step.py` | `per_team` carried `runs`, unread by step 3 | step 3 shows runs too |
| Gallery, `unchecked_derived`'s docstring | `steps` carried `run_id`, unread | counts `COUNT(DISTINCT steps.run_id)`, and says why |
| How-to 18, step 8 (Python, its Hive not shown) | `changes` carried minutes and minutes_before, unread | the Statement shows all five |
| Copilot 03's W2 (Python) | `ends` carried `job_id`, unread | `SELECT(job_events.event_type)` |
| Copilot 12's W2, T2 | a Total Row's CTE carried every column | selects only the columns totalled |
| Copilot 15's W2 | `ok_runs` carried run_id, duration_mins | `SELECT job_id ...` |

No `SELECT *` in a CTE, no ORDER BY without LIMIT in a CTE or subquery, and no CTE read twice
in any doc block; the README template, the Workflows overview and the Example projects (page
and `.hql` files) held none of the four. Kept, with why (also `KEPT` in the test):

- **How-to 05, step 7**: the Building block `runs_per_job` carries dt, runs and minutes the
  team Statement doesn't read. A block serves several Statements, a row for each job and day,
  as step 6's check of one day reads it; the pruner drops runs and minutes; dt gives the team
  Statement a row a day to add up, the same totals.

### The code path

- **Fixed: -IFS forms over one Table's same groups, other conditions** (found by the test in
  X67, X69 and F9's own test; ticket 04's code): two LEFT JOINs each reading the Table, or its
  step CTE, are one, each total over its own conditions' rows, `SUM(CASE WHEN .. THEN v END)`,
  `COUNT(CASE WHEN .. THEN 1 END)`; a form alone keeps its WHERE, so fewer rows are grouped
  (`workbook_formulas.totals_read`, `_aggregate_of_kept_rows`). The rows are the same: a group
  with no kept row gives NULL either way, COALESCE(.., 0) as before; every task still passes
  its scorer.
- **Fixed: W2 and T2's whole-Table CTE** (ticket 05 kept it): a Total Row's CTE carries only
  the columns its totals read (`workbook_totals.over_its_table`, `lean_ctes` with nothing held
  whole). A DISTINCT or UNION CTE is still kept whole, so the rows are the same.
- **Already lean: a step Table's CTE from ticket 04's `_with_steps`**: every final and level
  goes through `lean_ctes`, and the test finds no unread column in any task's or fixture's
  final.
- **Kept: PF5** (ticket 06), a Top or Bottom value filter's IN over a RANK reading the source,
  or the step's CTE, again (fixture 06's `ok_runs`, in `KEPT`): the totals of the kept items,
  an Average or a Distinct Count, need the kept rows before they are grouped.
- **Kept: two GETPIVOTDATA naming different items** (PG1), a LEFT JOIN of the pivot's CTE
  each, as one join matches a row on one key; and **a lookup (F8) and an -IFS total (F9) on one
  step Table**, a row's value and a group's total, which one join can't give. No task or
  fixture has either yet.

### For tickets 13 and 14: each Copilot file change (ADR 0016, both paths the same Hive)

| File, rule | Change | Code, and its test |
|---|---|---|
| 11's F9 | "several grouped on t's a: one join, each `SUM(CASE WHEN s = 'x' THEN v END)`, as Hive reads t again for each join" | `totals_read`, `test_f9_forms_on_one_table_s_groups_share_one_read_of_it` |
| 12's T2 | the Table's final read "as a CTE that selects only the columns totalled" | `over_its_table`, `test_t2_a_total_row_is_a_final_of_its_own_reading_the_tables_final_as_a_cte` |
| 12's W2 | `by_job` selects `COALESCE(c.runs, 0) AS runs` alone | `test_file_12_w2_a_summarys_total_row_reading_its_final_as_a_cte` |
| 15's W2 | `ok_runs` selects `job_id` alone, as ticket 05's table asked | `lean_ctes` |
| 15's H1 to H5, C10 | new: each step read once, forms grouped alike one join; a CTE's columns each read after it, no `*`; each WHERE in the SELECT reading its source; no CTE that only copies a step; no ORDER BY without LIMIT in a CTE or subquery, no DISTINCT for a join's repeats | `tests/repo/test_lean_hive.py` holds the code to H1, H2 and H5 |

Ticket 14 scores 11, 12 and 15 again on the Excel tasks. Files 01 to 10 changed too (A11 and
the trims above), for the Copilot evaluation's next round, as `docs/copilot-eval.md` says.

### The test

`tests/repo/test_lean_hive.py` reads with sqlglot each `hive` and `output` block of
`docs/main/`'s pages (the how-tos, the gallery, the Example projects page, the Workflows
overview), each ```sql block of `docs/` and `copilot/`, each Example project `.hql`, and each
final `workbook_hive` writes for every Excel evaluation task (`excel_eval_tasks.TASKS`, built by
`formula_workbook.saved`) and for each workbook fixture. It fails on a CTE read more than once,
a `SELECT *` in a CTE, a CTE column nothing after it reads (a DISTINCT or UNION CTE, or one a
`*` reads, left alone), and an ORDER BY with no LIMIT in a CTE or subquery, naming the file and
block, or the task and final. `KEPT` lists the two that stay, and a test fails on a kept one
that is gone. A line of a query a page shows alone, as `execute: WITH ...`, is passed over.
**Left for the lead:** `excel_eval_tasks.py`'s own reference Hive (`task.finals`) isn't read,
as ticket 10 is making it lean; add it once both merge.

### What a beginner sees that changed

How-tos 04, 05, 09, 18 and 25 (step 4 new, 5 to 10 renumbered), `unchecked_derived`'s
docstring, the gallery's step_by_step, and Copilot files 01 to 12 and 15. The beginner reader
ran on the draft (Opus, 58,164 tokens, 195 s), each stop answered:
[its report](../reports/beginner-reader-2026-11-19-ticket-17.md).
