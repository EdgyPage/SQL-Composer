# A pivot is one table, its totals left out

Type: task
Status: resolved
Blocked by: 06, 10, 11, 14
Size: L

## Question

The user (2026-11-19), after opening the pivot fixtures in Excel: "I saw a lot of grand totals
and I want to be sure we're aligned. I didn't see many tables without grand totals. I want
sensible transformations of pivot tables to the rows of a table, not necessarily a one to one
recreation. A one to one recreation would be difficult to do with some many nested rows in the
pivot field." Asked, the user chose: one table, no totals; and an Average's, a Distinct Count's
or a % of total's totals left out too.

How a pivot converts now that its totals are never tables (map Notes, "Totals"; ADR 0016).

## Done when

- **The code path**: a pivot's final is its rows at the finest grain, each Row and Column field a
  column, each value a column, as ticket 06's PR and PV rules write them; no total-level final
  (`<pivot> (grand total)`, `<pivot> (by <field>)`) is made. Each total the pivot shows is a
  checklist note naming it and the GROUP BY of the converted table (or of the source, for a
  total no sum of rows gives: an Average, a Distinct Count, a StdDev, a % of total) that gives
  it, and file 21's rollup as the way to grow it. PL1 and PL2 change to say this; PV8 (NULL at a
  level) and PC3 (an item added into a total) go, or say what's left of them; Show Values As
  stays a Window over the pivot's rows.
- **Both paths equal**: file 20's rules change with the code, in the same commit; the tie test
  holds; files 21 and 22 drop any total-level table they name.
- **The tasks** (ticket 10's): each pivot task's references drop their total-level finals, and the
  scorer stops asking for them; a reply that adds a total-level query is not wrong for it.
- **The Workbook check** compares a pivot's body cells, never its total cells, and says so in one
  line; its tests follow.
- **The Pivot filter Decision** and the convert workflow (tickets 07 and 08): no total-level table
  to rename, copy or answer; their tests follow.
- **The docs** (ticket 15's how-to 33 and pages) regenerated where they showed a total table.
- Tests: a pivot with both Grand Totals and subtotals converts to one table; each total named;
  the stored body cells match; the evaluation's pivot tasks score on the code path.

## Answer

Built 2026-11-19 on dev's 3d7e8834 (ticket 16 merged), test first.

### The code path

- `workbook_pivot_hive.py`: a pivot's final is its rows at the finest grain, as before; no
  total-level final is made (`write_pivot_total_finals`, `level_final_name`,
  `GRAND_TOTAL_FINAL` and `LEVEL_RULES` gone). `add_pivot_total_notes` adds one map note a
  total (kind left alone, rule PL2, on the pivot) for each total `levels_shown` gives, and one
  for a field's subtotals of functions the person chose (no longer refused). A total's note
  gives the GROUP BY of the pivot's table where every value is a plain Sum, Count, Max or Min
  (`OVER_THE_ROWS`: SUM, SUM, MAX, MIN of the table's columns); else the source's GROUP BY,
  `level_select` at that level, with the CTEs of the final it reads, leaned, saying the value
  isn't a sum of the rows. A Running Total, Difference From or Rank without its base field is
  named blank; a calculated item outside the total is named as added into Excel's total.
  `level_select` keeps the NULL-at-a-total and the item-added-in Hive only for GETPIVOTDATA of
  a total (PG2), with no note. Show Values As stays a window over the table's rows.
- `workbook_conversion.py`: a PL2 note's Next is "nothing to do, unless you need it: run the
  query, or keep every total in one table as Copilot file 21's R9 says";
  `WorkbookFinal.totals_read` and `notes_retargeted_to` write each total's query reading the
  dev table by its full name in the checklist, so a "name" answer renames it with the table.
- `workbook_check.py`: compares a pivot's body cells only (`_is_body_cell`), counts its total
  cells in `CheckedFinal.totals_not_compared`, and says so in one line.
- Tickets 07 and 08: no total-level table to name, rename or answer. The rename family keeps a
  Total Row's table, now with a test of its own
  (`test_answering_a_name_renames_the_table_and_its_total_row_with_it`). `write_decisions`'
  docstring, `decisions.NAME_COMMENT` and `proposed_name_note` say "its Total Row's table, if
  it has one".

### The checklist's total notes, as a person reads them (fixture 04)

    From the workbook, left alone (rule PL2, in Copilot file 20): PivotTable1: its grand total
    is left out of its table: `SELECT SUM(sum_of_duration_mins) AS sum_of_duration_mins FROM
    mart_dev.pivot` gives it. Next: nothing to do, unless you need it: run the query, or keep
    every total in one table as Copilot file 21's R9 says.

The other shapes: "its grand total is left out of its table, and Distinct Count of job_id
isn't a sum of its rows: `SELECT COUNT(DISTINCT job_id) AS ... FROM <database>.job_runs` gives
it, from the source"; "its total by dt is left out of its table, and Excel shows it blank";
"... gives it, without the calculated item done, which Excel's total has added into the total,
its items counted twice"; "its subtotals of dt, Sum and Count, are left out of its table: each
is its function of the source's rows by dt". The Workbook check's line: `mart_dev.pivot, from
PivotTable "PivotTable1": its totals, 6 cells, not compared: its table holds the PivotTable's
rows alone, each total left out, as its checklist says.`

### Rule IDs (file 20, the code and the tie test in one commit)

- **PL1** restated: a pivot is one table, its totals left out; never a total row, a ROLLUP or
  a block for a total. **PL2** restated: each total named under Left alone with the GROUP BY
  giving it, of the table, or of the source for an Average, a Distinct Count, a StdDev or Var,
  a Calculated Field or Show Values As; blank; added into the total; file 21's R9.
- **PV8** and **PC3** removed, from file 20 and their tests; what is left of them is PL2's
  blank and added-in cases, and PG2's "the source's GROUP BY as Excel totals it".
- **PG2** restated; P3 now `PV1 to PV7`, P4 `PC1, PC2`; the term Total level is Total; W1 is
  one table with its totals named, a new W2 a total no sum gives; C1 and C2 follow. File 20 is
  8,018 characters. File 15's P13: "final, its totals left out" (8,998); file 21's Total term
  and R9 restated; files 22 and 24 named no total table.

### The tasks and the scorer

The 40 pivot tasks' references drop their 55 total-level finals; the scorer asks only for what
the references hold, and `test_a_reply_that_also_writes_a_pivots_total_is_not_wrong_for_it`
holds that an extra total query costs nothing. The stored-values test compares body cells
only. The wrong answers on X100's grand total and X108's `(by dt)` are now X100's Distinct
Count written as a count and X108's share over each day. X92 and X120 keep their ADDED_IN mark,
which the code path's note now says: both are out of `HELD` and pass, so all 40 pivot tasks
pass on the code path. `tests/repo/test_lean_hive.py`'s kept breaks lose the total levels (X104,
X122) and X91's and X111's reference steps, which only the totals made. `docs/copilot-eval.md`'s
Excel section follows. Memo keys: file 20 and the pivot tasks changed, so ticket 14's pivot
rounds are best run after this.

### On ticket 20, every generated output at 8.9 (2026-11-20)

Rebased onto dev's 3e478d74 (ticket 20): `write_decisions`' docstring and the module docstring
of `workbook_conversion.py` keep both tickets' words, and `WorkbookFinal` keeps ticket 20's
`sources` (each a SOURCES Decision) beside this ticket's `totals_read`. Then one regeneration
with the tools: both Example projects, `docs/main/*.html`, the README charts, the Copilot files
and the all-in-one, and the usability scenarios (H2's `key.json` at 8.9). The section below is
settled by it. `tests/snapshot/known.txt` is the union of both sides, pruned of what the test
set below made on dev and no longer makes. `test_example_projects_page.py`'s committed-page
test fails under `-n 6` on dev and here alike, its notebook stopping at "No module named
'warehouse'" when another test in the worker runs first; alone, or with the Example project
and how-to tests in one process, it passes.

### For ticket 15's outputs: regenerate after this merges

On this branch `test_example_projects.py::test_the_committed_project_is_what_the_generator_writes[intermediate]`
and `test_example_gallery.py::test_the_committed_gallery_is_what_the_generator_writes` fail,
their generated files holding the old words: `example_projects/intermediate/` (the job_hours
batch's Table reference NAME comment and its checklist, and PL2 notes if its pivot shows
totals) and `docs/main/examples.html` (`write_decisions`' docstring); by the same words, check
`docs/main/example_projects.html` and `docs/main/how_to.html`. Their snapshot hashes follow the
regenerate.

### Tests

The workbook, pivot, convert, decision, check and code-path tests, `test_excel_eval.py`,
`test_copilot_files.py`, `test_eval_rounds.py`, `test_eval_ladder.py`, `test_eval_sources.py`,
`test_usability_loop.py`, `test_workflows_page.py`, `tests/sqlglot_checks` and `tests/repo/`:
5,208 passed, 3 skipped. `tests/snapshot/known.txt`: 143 hashes added, and the 242 those tests
made on dev and make no more taken out. Not run: the whole suite; the code-review skill and the
beginner reader (a checklist note, a Workbook check line and `write_decisions`' docstring
changed) are the lead's.
