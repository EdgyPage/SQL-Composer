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
| A CTE carries only the columns read after it; no `SELECT *` | Kept, as a reading and debugging rule, said so: the column pruner is always on (`hive.optimize.cp` removed in 0.13, HIVE-4113), so Hive drops a column only carried where it works the CTE out in place. Hive work only where the CTE groups by the column (a row per value) or Hive materializes it (4.1); a short CTE is the one a person debugs, the user's hour. | Configuration Properties, `hive.optimize.cp` |
| Filter (a Partition first) and group before joining | Kept. A map join needs the small side under `hive.auto.convert.join.noconditionaltask.size`, 10 MB; else Hive joins in the reducers, where "the last table in the sequence is streamed through the reducers where as the others are buffered" (the Joins page); aggregates are not pushed below a join (`hive.transpose.aggr.join`, false). `hive.optimize.ppd` (true) pushes a WHERE down, but a WHERE on a LEFT JOIN's right side makes it inner (the Joins page's ds example). | LanguageManual Joins; HiveConf 3.1.3 (map join size, `hive.auto.convert.join`); HiveConf master (`hive.transpose.aggr.join`) |
| A chain of CTEs each copying the table to rename or add a column is one SELECT | Kept, as a rule for reading, not a Hive setting, said so: inlined, the copies cost Hive little; each is one more step to debug. No Hive doc. | - |
| No ORDER BY in a CTE or subquery without a LIMIT | Kept. ORDER BY's total order goes through one reducer; from 3.0 `hive.remove.orderby.in.subquery` (true, HIVE-6348) drops one with no LIMIT in a subquery or view, so it sorts nothing anyway; strict mode wants a LIMIT on any ORDER BY. | LanguageManual SortBy; Configuration Properties |
| No DISTINCT to undo a join's fan-out | Kept, as a rule for the rows, not a Hive setting, said so: the join makes every repeated row, then DISTINCT sorts them all to drop the copies, and drops rows rightly alike too. No Hive doc. | - |

Written once, short, with why:

- **Copilot files 01 to 10**: rule A11, the shortest line that says what to do, with no
  reason (the reasons are file 15's and the how-to's), right after the Always block:
  `tools/copilot_sources/_lean.txt`, a new `{lean}` placeholder (`tools/copilot_files.py`),
  in 01, 02, 04 and 06 to 10: "Read each Derived table once; SELECT in it only what is read
  after; filter and group before joining; fix rows a join repeats by its whole Key or a total
  first, not SELECT_DISTINCT." Files 03 and 05 haven't room for it, so each writes a shorter
  A11 there itself: 03 "Read each Derived table once; SELECT in it only what is read after;
  filter and group before joining." (03 joins nothing: file 04 does); 05 "Read each Derived
  table once; SELECT in it only columns read." No other rule is shortened. The Always block's
  heading says A1 to A11, and file 09's "A1 to A10" is "A1 to A11". A6 already holds
  ORDER_BY's LIMIT. `test_each_objective_file_has_the_same_parts` holds A11 after the block.
- **Files 11, 12 and 15**, loaded together, which write Hive: rules H1 to H5 and self-check
  C10 in file 15 (`## Rules: Hive that stays small`), each with its reason as the sources give
  it: H1 "Hive works a CTE out at each read (4.1 keeps one with totals read over 3 times)"; H2
  "Hive drops the rest, but a short CTE is quicker to check"; H4 "For reading"; H5 "Hive
  drops" an ORDER BY with no LIMIT in a subquery. Files 00, 13, 14, 16 to 19 write no
  Statement or Hive of their own to sweep.
- **How-tos**: Keep reads and joins fast's new step 4, "Keep each step small": a worked example
  (`events_per_job` grouped before its join) and the six rules with their reasons; a pointer in
  Count, join and stay safe (joins, step 10), Look across rows (windows, step 8), Convert
  someone else's Hive (step 13: a Conversion keeps each script's shape; make it lean once it
  passes) and Share Building blocks (step 2).

### The sweep

Read by the new test (below), every block, string and span. Breaks found and fixed:

| Where | Break | Fix |
|---|---|---|
| How-to 05, step 2 | `job_totals` carried `runs`, unread | carries job_id and minutes |
| Gallery, `statements/step_by_step.py` | `per_team` carried `runs`, unread by step 3 | step 3 shows runs too |
| Gallery, `unchecked_derived`'s docstring | `steps` carried `run_id`, unread | counts `COUNT(DISTINCT steps.run_id)`, and says why |
| How-to 18, step 8 (Python, its Hive not shown) | `changes` carried minutes and minutes_before, unread | the Statement shows all five |
| Copilot 03's W2 (Python) | `ends` carried `job_id`, unread | `SELECT(job_events.event_type)` |
| Copilot 12's W2, T2 | a Total Row's CTE carried every column | selects only the columns totalled |
| Copilot 15's W2 | `ok_runs` carried run_id, duration_mins | `SELECT job_id ...` |

**Docs changes a person sees in a result:** how-to 18's step 8 shows two more columns,
minutes_before and minutes, beside the change, and the gallery's step_by_step step 3 shows
runs beside minutes: each Statement now reads what its Derived table carries, the rows the
same. `unchecked_derived`'s docstring (help() and the gallery) counts `COUNT(DISTINCT
steps.run_id)` per step, and says why. How-to 05's step 2 Derived table shows two columns, not
three.

No `SELECT *` in a CTE, no ORDER BY without LIMIT in a CTE or subquery, and no CTE read twice
in any doc block; the README template, the ADRs, the Workflows overview, the Copilot files'
other fences, indented blocks, Python strings and spans, and the Example projects (page and
`.hql` files) held none of the four. Kept, with why (also `KEPT` in the test):

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
  or the step's CTE, again (fixture 06's `ok_runs`, and since ticket 10 tasks X104's
  `by_job_day` and X122's `job_runs`, each in its four finals, in `KEPT`): the totals of the
  kept items, an Average or a Distinct Count, need the kept rows before they are grouped.
- **Kept: two GETPIVOTDATA naming different items** (PG1), a LEFT JOIN of the pivot's CTE
  each, as one join matches a row on one key; and **a lookup (F8) and an -IFS total (F9) on one
  step Table**, a row's value and a group's total, which one join can't give. No task or
  fixture has either yet.

### For tickets 13 and 14: each Copilot file change (ADR 0016, both paths the same Hive)

Each Copilot file's change, for ticket 14's round (and the Copilot evaluation's, for 01 to 10):

| File | Change |
|---|---|
| 01, 02, 04, 06, 07, 08, 10 | A11 (`_lean.txt`) after the Always block; the block's heading A1 to A11 |
| 03 | its own shorter A11; W2's Derived table `ends` selects `event_type` alone |
| 05 | its own shorter A11 |
| 09 | A11 (`_lean.txt`); its "A1 to A10" twice is "A1 to A11" |
| 11 | F9: several forms grouped on one column share one join |
| 12 | T2: the Total Row's CTE selects only the columns totalled; W2's `by_job` so |
| 15 | W2's `ok_runs` selects `job_id` alone; rules H1 to H5; self-check C10 |

Tied to the code, for ticket 13:

| File, rule | Change | Code, and its test |
|---|---|---|
| 11's F9 | "several grouped on t's a: one join, each `SUM(CASE WHEN s = 'x' THEN v END)`, as Hive reads t again for each join" | `totals_read`, `test_f9_forms_on_one_table_s_groups_share_one_read_of_it` |
| 12's T2 | the Table's final read "as a CTE that selects only the columns totalled" | `over_its_table`, `test_t2_a_total_row_is_a_final_of_its_own_reading_the_tables_final_as_a_cte` |
| 12's W2 | `by_job` selects `COALESCE(c.runs, 0) AS runs` alone | `test_file_12_w2_a_summarys_total_row_reading_its_final_as_a_cte` |
| 15's W2 | `ok_runs` selects `job_id` alone, as ticket 05's table asked | `lean_ctes` |
| 15's H1 to H5, C10 | new: each step read once, forms grouped alike one join; a CTE's columns each read after it, no `*`; each WHERE in the SELECT reading its source; no CTE that only copies a step; no ORDER BY without LIMIT in a CTE or subquery, and a join's repeats fixed in its ON, not by DISTINCT | `tests/repo/test_lean_hive.py` holds the code to H1, H2 and H5 |

### The test

`tests/repo/test_lean_hive.py` reads with sqlglot:

- each `hive` and `output` block of `docs/main/`'s pages (the how-tos, the gallery, the
  Example projects page, the Workflows overview);
- in each Markdown file of `docs/` (the README template and the ADRs among them) and each
  Copilot file: every fenced block of any language, each string of a ```python block, every
  indented block and every backticked span; a piece with `...`, such as file 07's P2, is no
  whole query and is passed over. Files 20 and 21 are read once they exist (`copilot/*.txt`);
- each Example project `.hql`;
- the Excel evaluation's reference Hive (`excel_eval_tasks.TASKS`' `finals`), and each final
  `workbook_hive` writes for every task and workbook fixture.

It fails on a CTE read more than once, a `SELECT *` in a CTE, a CTE column nothing after it
reads (a DISTINCT or UNION CTE, or one a `*` reads, left alone), and an ORDER BY with no LIMIT
in a CTE or subquery, naming the file and block, or the task and final. It reads the shapes on
its own, apart from `lean_hive.py`, on purpose, a check written a second way. What stays:
`KEPT` (the Building block, PF5's nine finals) and `REFERENCE_STEPS`, the reference Hive's
shared steps in 13 tasks (X67 to X75, X77, X78, X91, X111), whose CTE is one text for each
final of its task, each final reading its own columns; the scorer compares rows alone and no
person reads it. Making each final's copy lean is left to a ticket of its own. A test fails on
a kept break that is gone.

### What a beginner sees that changed

- How-to Keep reads and joins fast: step 4 is new, "Keep each step small", a worked example
  and six rules with their reasons; steps 5 to 10 are renumbered; the Goal and "When you'd
  use it" name it.
- How-to Share Building blocks, step 2: the Derived table job_totals has job_id and minutes,
  with a paragraph on why.
- How-to Look across rows, step 8: the result shows minutes_before and minutes beside change.
- How-tos Count, join and stay safe (step 10) and Convert someone else's Hive (step 13): a
  few sentences pointing at the rules.
- `unchecked_derived`'s docstring, in help() and the gallery: it counts `COUNT(DISTINCT
  steps.run_id)` per step, and says why.
- The gallery's step_by_step: step 3 shows runs too.
- Copilot files: A11 in 01 to 10, the code's lean shapes in 11, 12 and 15, H1 to H5 in 15.

The beginner reader ran on the draft (Opus, 58,164 tokens, 195 s), each stop answered:
[its report](../reports/beginner-reader-2026-11-19-ticket-17.md).

## Review

The code review's findings (2026-11-19), each answered after rebasing onto dev's 192d4b9c
(tickets 05's review, 06 and 10, the VAR_SAMP fix):

1. **No other rule trimmed to fit A11.** Files 03 and 05 are as dev holds them (05's R1, R2,
   R6, R7, C4, its Objective and Load lines; 03's `at_least`, its Load line and `t` term) and
   A3 has "comparisons are A4's" again. A11 is the shortest line that says what to do, in
   `_lean.txt` through a `{lean}` placeholder; 03 and 05, with no room for it, write a shorter
   A11 of their own (above). Every file is within 9,000; regenerated and merged; each file's
   change is listed above for ticket 14.
2. **Only what the sources support.** H1 and the how-to say CTEs are worked out at each read
   up to 4.0 and 4.1 keeps one with totals read more than 3 times: the setting's text is
   "exceeds this threshold", 3, so four reads or more, not three. A11 gives no reason, so
   nothing it says outruns a source. H2 and the how-to's rule 2 say the column rule is for
   reading and checking (Hive drops what no one reads), Hive work only for a grouped column or
   a saved CTE; the chain-of-copies and DISTINCT rules say they are for reading and for rows,
   not a Hive setting; the reduce-side join line says the reducers buffer every table but the
   last and stream the last, as the Joins page does.
3. **The test reads all of it**: every fence, Python string, indented block and span of the
   Copilot files and `docs/` Markdown (the README template among them), and the evaluation's
   reference Hive. New breaks found: PF5 in tasks X104 and X122 (kept, with fixture 06's), and
   the reference Hive's shared steps (kept as `REFERENCE_STEPS`, with why, rather than made
   lean here: that is the reference's own ticket, whose rows the scorer alone reads). No new
   break in a Copilot file outside its ```sql fences. Files 20 and 21: read once they exist.
4. **One way per job.** `_conditional_aggregate` builds a form's aggregate and calls
   `_aggregate_of_kept_rows`, the one place a total is put over the rows its conditions keep,
   which `totals_read` calls too when it merges totals into one join. The test's docstring
   says it reads CTEs apart from `lean_hive.py` on purpose; `names_read_after` gives a
   `NamesRead` (`names`, `every_column`).
5. **File 05's R2** is dev's again, wrapped as the file is.
6. **Docs changes named**: the paragraph "Docs changes a person sees in a result" above.

`tests/snapshot/known.txt` is dev's, plus the 29 hashes the branch's tests make that it
doesn't know, less the 26 only dev's code made (both runs of the same test files, CI=1).
