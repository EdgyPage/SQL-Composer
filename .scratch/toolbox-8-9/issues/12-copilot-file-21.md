# Copilot file 21: growing a converted pivot

Type: task
Status: resolved
Blocked by: 08, 11, 17
Size: M

## Question

What Copilot adds to a pivot after it is converted, and how a Pivot filter scales (round 1, Q8;
round 3, Q4; the user's "copilot hint that the filter or sliced views could be aggregated in to
batched inserts on a table or different tables").

## Done when

- **`tools/copilot_sources/21_*.txt`**, at most 9,000 characters, loaded with 03, 05 and 06,
  writes Toolbox code in the converted Table notebook, never a change to the workbook:
  - add-ons: % of a total, running totals, ranks, a calculated field, date grouping, the wide
    shape of a Column field, totals as a rollup Statement;
  - Pivot filters at scale: each proposal of ticket 08's Decision, when to pick it, and each
    layer's table count, with "a filter with 100 conditions would make 100 tables, but the
    higher layer filter may have only 3, which is manageable";
  - what no Decision does: two pivots differing only in their filter made one table, written
    as batched inserts.
- **`00_start_here.txt`** says when to load it.
- **Its tasks** in `tools/copilot_eval_tasks.py`, dev and held-out, scored as the other files'
  are.

## Answer

(The Review below split file 21 in two, 21 the add-ons and 22 the Pivot filters and batched
inserts, and changed the evaluation's names; where the two differ, the Review holds.)

Built 2026-11-19 on dev's 3c60c691 (ticket 08 merged). No evaluation round ran: ticket 14 runs
it.

**The file.** `tools/copilot_sources/21_growing_a_converted_pivot.txt`, written to
`copilot/21_growing_a_converted_pivot.txt`: 8,809 characters, 8,996 with Windows line breaks (4
to spare). In files 03, 05 and 06's shape:

- **Patterns** P1 to P12, each pointing at a rule or Worked pattern.
- **Terms**: converted pivot (a Saved table convert made from a PivotTable, its logic cell's
  rows() read by create(), preview() and write()), Pivot filter and its Decision, layer, `d`
  and `t`.
- **Rules: add-ons**, each as files 03 and 05's functions write it, in the converted Table
  notebook's logic cell: R1 change rows() and the Derived tables above it, never the
  workbook, never a convert again (the workbook is a one-time way in); R2 a column added goes
  in the Table reference, a share or rank in does_not_add_up, a table created in dev changed
  first by file 14; R3 **a Window over the pivot's sums reads them from a Derived table**
  (no sum_of inside a sum_of, as `window`'s docstring says), % of the grand total over
  `window()`, of a row or column total `window(PARTITION_BY=...)`; R4 Running Total In; R5
  Rank; R6 a Calculated Field over the sums; R7 `month_start`, `week_start`; R8 the wide
  shape of a Column field, `sum_of(..., where=equals(...))` a column per value, and why
  convert wrote rows; R9 every total level in one Statement, `cube` for Rows and Columns with
  both Grand Totals, `rollup` for Rows with subtotals, in place of the level tables; S1 to
  scale, dt in the grain and the table partitioned by it, a day a run (file 06's R6).
- **Rules: Pivot filters at scale**, ticket 08's four answers in its words: F1 answered by
  field in DECISIONS, then `project.write_decisions(...)`; F2 "keep", proposed, 1 table; F3
  "fold", like dragging the field from Filters to Rows, 1 table; F4 "batch", 1 table, a
  Partition per value, its Script tag's answer proposed (file 17); F5 "tables", like Show
  Report Filter Pages, `<table>_<value>`, at least one per value the cache held, two layers
  multiplying ("Region 3 and Site 100 make at least 300"), with the user's sentence in bold,
  "A filter with 100 conditions would make 100 tables, but the higher layer filter may have
  only 3, which is manageable", and ticket 08's which-to-pick (a handful "tables", a hundred
  "fold" or "batch"; say each count first); F6 a value filter's two answers, and no "tables"
  for a .hql converted alone. Each answer's "Pick it when" line is the checklist note's.
- **Rules: what no Decision does**: B1 pivots the same but for their filter's values are one
  table partitioned on the field, one write filling each Partition, a pivot's rows each, a
  reader of one reading its Partition; B2 one Partition a write,
  `INSERT_OVERWRITE(t, partition={...})` over rows(value), the value a constant or a Run value.
- **Always**: A1 to A10 named as files 03, 05 and 06's, which are loaded with it, and A11
  (`{lean}`) itself. The other objective files hold `{always}`; this one has no room for it
  beside its three files, which hold it already, so `test_each_objective_file_has_the_same_parts`
  exempts it and checks its A11 instead.
- **Names**: derived, window, rank, month_start, week_start, rollup, cube,
  project.write_decisions.
- **Worked patterns** (no task's tables): W1 rows() with each job's share of its day, a
  Window over a Derived table, lean (one read, only the columns read after); W2 two pivots,
  eu and us costs of ops.region_costs, one table partitioned by region, its read bounded by
  the region; W3 the decisions cell, one table's status folded and another's region a table
  per value. W1 and W2 run on the Example database; W3 calls a Project action, so it is read.
- **Steps, Output, Self-check** C1 to C4.

**File 00** (8,849 characters, 8,989 with Windows line breaks, 11 to spare): Index P19, "a
table made from a PivotTable, "add % of total"", loads 21, 03, 05, 06; step 1 is done "when you
have each file its row names", and C1 "its first messages are the files the Index row names",
for a workbook and for 21 alike; Which file names 21, "loaded with 03, 05 and 06". To fit, words
moved out of three Which file lines: 17's drops the Run value's definition, which Terms gives;
18's "the Statements it runs" is "its Statements"; 19's drops its list of what it asks (P16
still routes it). Not split.

**Its tasks** (written before any tuning; references pass, and a wrong answer of each kind
fails): objective `21`, "growing a converted pivot", in `tools/copilot_eval_tasks.py`:

- T50 (dev, logic): % of the grand total added to a converted pivot's logic cell, its clauses
  as convert wrote them pasted in.
- T51 (dev, logic): two pivots differing only in their slicer, one table partitioned by
  status, both Partitions in one write.
- T52 (dev, workflow): a Copilot .hql of a pivot converted alone; its slicer's Decision
  answered "fold", with its location.
- T53 (held out, logic): the wide shape of a Column field.
- T54 (held out, workflow): a Report filter's Decision answered "batch".

The logic tasks compare one day (`partition={"dt": "2026-09-24"}`), as a converted pivot reads
every day.

**The evaluation loads 21 with 03, 05 and 06** (`tools/copilot_eval.py`): `LOADED_WITH`,
`files_of(objective)` and `file_text(number)`; arm C's `shared_text` joins an objective's files,
`files_loaded` gives each by its number, and the proxy is asked for `Used: 21:R3, 05:W2`-style
ids where there are several files. Every other objective loads its one file, as before, so no
other task's memo key changes. `index_loads` now reads a row as its first file's: a row's
other files are allowed for it, and each for itself, so a task of 03 never passes the Index by
naming 21 (P19's row names 03); `test_eval_rounds` checks 15's and 21's rows.
`docs/copilot-eval.md` says so in its arm, Index, memo and by-hand lines.

**Tests run:** `tests/test_copilot_files.py` (range 22; file 21's answers and the user's words;
00 loads 21 with the files `files_of` gives), `tests/test_copilot_eval.py` (54 tasks, 21 three
dev and two held out), `tests/test_eval_rounds.py` (the Index's rows; arm C's four files),
`tests/test_eval_sources.py`, `tests/test_excel_eval.py`, `tests/repo/`. Not the whole suite.
`tests/snapshot/known.txt`: dev's, plus the 31 new texts W1, W2 and the five references make.

**Left for ticket 14:** file 21's first round (dev T50 to T52, then held-out T53, T54), and
arm R for the five. File 21 and 00 have 4 and 11 characters to spare: a tuning line that
outgrows 9,000 splits the file.

## Review

The coordinator's review (2026-11-19), each finding answered in `fix(8.9): ticket 12's
review: ...`, rebased first onto dev's d43fa9a5 (the Workbook check's reading of an answered
Pivot filter's table). File 21 had to say what ticket 08 does, both paths equal, which didn't
fit in 9,000 characters, so **file 21 is split in two** (the user's standing rule): example
prose went first, no rule was cut.

- **`21_growing_a_converted_pivot.txt`** (6,869 characters, 7,017 with Windows line breaks):
  the add-ons, loaded with 03, 05 and 06. Patterns P1 to P9 (P9 sends a Pivot filter or one
  table of two pivots to file 22); Terms (converted pivot, total level); R1, R2 where an
  add-on goes; R3 to R9 and S1 each add-on; Always (A1 to A10 pointing back to the Load line,
  then A11); Names; W1 rows() with each job's share of its day and its rank in the day; W2
  rows() grouped by month; Self-check C1 to C3.
- **`22_pivot_filters_at_scale.txt`** (7,372 characters, 7,521 with Windows line breaks): the
  Pivot filters at scale and batched inserts, loaded with 06 (saving a table) and 17 (Run
  values and the decisions cell). Patterns P1 to P8; Terms (Pivot filter and its Decision,
  layer, Partition, Script tag); F1 to F7 the four answers; D1 to D4 answering; B1, B2 what
  no Decision does; Always; Names; W1 the decisions cell, W2 two pivots one table; Steps (a
  Count step for "tables"), Output, Self-check C1 to C3.

The findings:

1. **F6 is two cases** (22's F6, F7): a value filter (Top 10) has only "keep" or "fold", as
   its ranks change with the rows; a filter of a Copilot .hql converted without its workbook
   has no count, so not "tables": answer "fold" or "batch", or convert the .hql beside its
   workbook.
2. **Ticket 08's answering rules** (22's D1 to D4): "fold" and "batch" refused for a filter
   in a step, a CTE other parts of the query read ("keep" or "tables", or move the filter out
   of the step, as `answer_problem` says); a Key you answered kept while it still fits, else
   proposed again, open, `"key": "proposed"` accepting it; once the table is created in dev,
   another answer refused; answering again with another answer undoes "tables", its other
   tables gone and the first renamed back.
3. **F4's proposal**: once "batch" is written, check() pastes it: a Run value,
   `project.new_run_value("latest_dt", latest_partition="ops.job_runs.dt")` then `"DT":
   latest_dt`, where the field is a partition column of a table it reads (a Timeline's day),
   accepted for a day each run works out; else `"STATUS": hivevar("STATUS",
   default="FAILED")`, the first value kept, accepted when the scheduler gives each run its
   value.
4. **F5's names** as ticket 08 makes them: `<table>_<value>` in snake case, a blank
   `_blank`, a day `_2026_09_23`, a clash `_2`; two layers one per pair; a Timeline's days
   each make a table: count them first.
5. **R7**: `month_start` gives a day, 2026-09-01, where convert's Months grouping (ticket
   06's PR3) gave a label, Sep, adding up every year's September, so `month` is a new column,
   in place of the label's, in SELECT and the Table reference.
6. **R9**: the total levels' tables named as ticket 07 names them,
   `<table>_by_<field>` and `<table>_grand_total` (`TABLES` in
   `tests/test_convert_workbooks.py`: `pivot_by_job_id`, `pivot_grand_total`); a total's row
   NULL in each column it totals over.
7. **`index_loads`**: a row lets a task of each file it names load every file it names,
   except that a file some row names first is an objective of its own, which a later row
   loads only beside its own first file. So tasks of 11 and 20 still allow 15, 11, 12 and 20
   (the old assertion is back beside the new), and a task of 03, 05, 06 or 17 never loads 21
   or 22. Its docstring is plain sentences.
8. **One name each**: `copilot_eval.objective_files(objective)` and
   `excel_eval.workbook_files(task)`; `excel_eval.files_loaded` reads each file through
   `copilot_eval.file_text`, and its own `COPILOT` constant, now unread, is gone.
   `docs/copilot-eval.md` follows.
9. **Small**: each file names the files it is loaded with once, in its Load line, its Always
   line pointing back to it; one table of two pivots is 22's P7, pointing to B1.

**What followed the split.**

- **File 00** (8,836 characters, 8,977 with Windows line breaks, 23 to spare): Index P20, "its
  Pivot filter, "how many tables?"", loads 22, 06, 17; Which file names 21 (add-ons) and 22
  (Pivot filters, each answer's count, one table of two pivots). To fit: the Which file lines
  of 11, 12, 15, 20 and 21 no longer say what each is loaded with, which their Index rows say;
  Fitting Copilot says "one message to Copilot".
- **The evaluation**: `LOADED_WITH` is `{"21": ("03", "05", "06"), "22": ("06", "17")}`;
  objective `22`, "Pivot filters at scale, and batched inserts". T51, T52 and T54 are 22's (two
  dev, one held out); 21 keeps T50 (dev) and T53 (held out) and gains **T55** (dev, logic):
  a rank within each day added to a converted pivot, mart.job_day_ranks. 55 tasks, 36 dev and
  19 held out, each objective two dev and one held out but 07 and 13. All references pass.
- **Tests**: `test_copilot_files.py` (23 files; 21 and 22 exempt from the Always block, each
  holding A11; 00's rows for 21 and 22 against `objective_files`; file 22 says each of
  findings 1 to 4 and the user's words; file 21 says 6's names and 5's label),
  `test_copilot_eval.py` (the counts), `test_eval_rounds.py` (the Index's rows, 11 and 20 as
  before; arm C's files for T50 and T52), `test_excel_eval.py` (`workbook_files`).
  `tests/snapshot/known.txt`: dev's, plus the 37 new texts the files' blocks and the six
  references make, from the touched files run on one process.

**Left for ticket 14:** files 21 and 22's first rounds (dev T50, T55 and T51, T52; then
held-out T53 and T54), and arm R for the six tasks.
