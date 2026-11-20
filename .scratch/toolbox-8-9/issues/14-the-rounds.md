# The rounds: file 20 tuned, held-out scored, the code path scored

Type: task
Status: claimed
Blocked by: 09, 10, 11, 12, 13, 17
Size: L

## Question

Whether both paths reach the bar (round 3, Q9; "Both paths, equal").

## Done when

- **The Copilot path**: file 20 tuned on dev for at most two rounds, then the held-out split
  scored once on Haiku and Sonnet; 95%, or a design spec of what misses.
- **The code path**: the same tasks converted by `project.convert`, scored by the same scorer,
  with each run's Workbook check; every miss fixed or written up as a bug.
- **A manual round** in Copilot on the workbooks the user builds in Excel, kept in
  `.eval-local/`.
- Each round recorded in the ledger; results in `.eval-local/`, never in git.

## Comments

- At ticket 10's merge (2026-11-19), the code path on the 40 pivot tasks, scored by
  `excel_eval.score` as ticket 05's test scores its own: 32 pass; X90, X92, X102, X110, X111,
  X113, X119 and X120 don't, among them X90's running total's grand total (PV8), X92's
  calculated item added into its total not named (PC3's mark words), X102's summary Table
  `team_report` read from the database, and X119's Data Model Distinct Count. Each is a code
  or reference bug for this ticket to settle, both paths equal (ADR 0016).

## Answer

The code half, built 2026-11-19 on dev's 1c8a39d6 (ticket 12 and the follow-ups). The rounds,
the manual round and the ledger rows are the lead's; this ticket stays claimed for them.

### The splits

Two lines waited for room (ticket 13): file 12's Q2 `=` between two columns, and file 20's PV5
text order. Each file is split by job, rules whole, every rule ID unchanged:

| File | Now holds | Characters (Windows line breaks) |
|---|---|---|
| 12 `12_excel_power_query.txt` | Power Query alone: Q, G, S, M, X1, W1; Q2's `=` added; P6 points at file 23 | 7,342 |
| 23 `23_excel_totals.txt` (new) | whole-column totals and Total Rows: T1 to T4 as they were, the Total Row term, 12's W2 as W1, a new W2 (a share of a whole column's total), C1 and C2 | 3,026 |
| 20 `20_excel_pivot_tables.txt` | PivotTables but their filters; PV5's text order and PC2's COALESCE added; P6 points at file 24 | 8,016 |
| 24 `24_excel_pivot_filters.txt` (new) | Pivot filters: PF1 to PF5 and the `-- Pivot filter:` mark as they were, PF5's blank added, the Pivot filter terms, a W1 (hidden items and a Bottom 2, the blank shown), C1 and C2 | 3,563 |
| 11 | its Load line: "12 (Power Query), 23 (totals) and, for a PivotTable, 20" | 8,989 |
| 15 | its first line, Load line and step 5 name 23 and 24; W3 points at file 23's W1 | 8,998 |
| 00 | Index P18 without "slicer"; new P21 (a Total Row or "SUM(t[v])": 15, 11, 12, 23) and P22 (a PivotTable with a slicer, Filter or Top 10: 15, 11, 12, 20, 24); R6 adds 23 and 24; Which-file lines for 23 and 24, 12's "as Hive" without totals; to fit, the Which-file lines of 13, 14, 16, 17, 18 and 19 shortened | 8,995 |

The Excel evaluation (`tools/excel_eval.py`): `EXCEL_FILES` (15, 11, 12) stays what every task
loads; `TOTALS_FILE` 23 is loaded where the workbook has a Total Row or a formula totalling a
whole column (`has_a_total`, `WHOLE_COLUMN_TOTAL`, T1's functions over `t[v]`), `PIVOT_FILE` 20
where it has a pivot, `PIVOT_FILTER_FILE` 24 where a pivot has a Pivot filter
(`has_a_pivot_filter`); `ALL_EXCEL_FILES` is every one, in the order a task loads them, which
the tie test and `test_copilot_files.py` read. A test holds that file 23 is loaded for exactly
the tasks covering a whole column, Total Row, SUMPRODUCT or STDEV/VAR total, and file 24 for
exactly those whose references mark a Pivot filter. The convert checklist's rule files
(`workbook_conversion.RULE_FILES`) name 23 for T and 24 for PF.

Memo keys: files 11, 12 and 15 changed, which every Excel task loads, so every Excel task's
arm C key moved (as tickets 13 and 17 had moved them already); a task loads 23 or 24 only where
it needs it.

### The code path, scored

`tests/test_workbook_code_path.py` scores the pivot tasks with `excel_eval.score`, as ticket 04's
and 05's tests score the formula and query tasks, and holds that the three tests together score
all 124 tasks. **122 of 124 pass**; X92 and X120 are held (below), as strict xfails. The eight
misses at ticket 10's merge and how each is settled:

| Task | Miss | Wrong | Settled |
|---|---|---|---|
| X90, X110 | PV8's grand total | the code | already fixed by ticket 13 (PV8 "grouping by nothing: no FROM"); both pass. Their total-level finals go with ticket 18 |
| X92, X120 | PC3's mark: the map says "added into this total", file 20 and the tasks "added into the total" | the code's words | **ticket 18's**, not fixed: the user (2026-11-19) leaves every grand total and subtotal out of a pivot's table, so the total-level finals (PL1, PL2, PV8, PC3's "added into the total") go, in the code, file 20, the tasks and the check. Both are strict xfails in `tests/test_workbook_code_path.py`'s `HELD`, which ticket 18 takes out with the tasks it changes |
| X102 | the summary Table `team_report` read as `<database>.team_report`, which isn't a table | the code | file 15's R1 makes a Table whose only typed columns are those its GETPIVOTDATA matches on a summary; `summary_matches` now reads GETPIVOTDATA's `[@field]` items, so its groups are written in (`test_r1_a_table_typed_only_in_what_its_getpivotdata_matches_on_is_a_summary`); the built `getpivotdata` workbook and fixture 06's `job_hours` are summaries now too |
| X111 | a Bottom 2 whose items are TEST and the blank: `f IN (..)` drops the blank, as NULL is in no IN list | the code and file 20 | PF5: "If the pivot shows f's blank item: `f IS NULL OR` before it", in file 24 and the code (`_blank_shown`, from the pivot's saved cells, as PF2 reads a blank from the cache); `test_pf5_a_blank_item_the_value_filter_shows_is_kept_with_is_null`. Limit: the blank is kept as last saved; if it later ranks out it stays. An exact form needs a second subquery in the WHERE, which Hive before 2.2 refuses |
| X113 | a ratio item, FAILED/(SUCCESS+FAILED), on a job that never failed: NULL where Excel gives 0 | the code and file 20 | PC2: each item's sum `COALESCE(.., 0)`, as Excel reads an item with no rows as 0 (`_item_hive`; `test_pc2_an_item_with_no_rows_in_a_group_is_0_in_the_formula_as_excel_reads_it`, and PC2's text test) |
| X119 | a renamed Distinct Count in a Data Model pivot read as a DAX measure | the task's workbook | `tools/pivot_tables.py` saved the implicit measure under the value's new name; Excel renames only the data field and keeps the measure it made as "Distinct Count of job_id". `excels_caption` names the measure; the reader was right (`test_a_renamed_data_model_value_keeps_the_measure_excel_made_named_as_excel_names_it`, `test_a_renamed_data_model_value_is_its_measures_summary_under_its_own_caption`). For the manual round: a renamed Data Model value in a workbook the user saves in Excel confirms it |

No other task missed: the 84 formula, query and total tasks still pass.

### What the lead's rounds must ask

Files whose text changed since their last round, so the rounds ask only these:

- **01 to 10**: A11, ticket 17 (unchanged here).
- **11, 12, 15**: every Excel task's arm C (tickets 13 and 17, and this split).
- **20**: every pivot task, X85 to X124 (tickets 13, 17 and this split): file 20's tuning on
  dev, then held-out once. Ticket 18 changes file 20 and the pivot tasks again (no total-level
  finals), so the pivot rounds are best run after it.
- **23** (new): the tasks loading it, those with a Total Row or a whole column's total.
- **24** (new): the pivot tasks with a Pivot filter.
- **21, 22** (new in ticket 12): T50 to T55, never run.
- **00**: arm R's routing tasks (its Index and Which-file lines changed).

### Also

- Ticket 15's docs name the Excel files as "15, 11 and 12" (the README template's Excel steps,
  `docs/main/workflows.html` from `tools/workflows_page.py`): they need 23 and 24, as file 00's
  R6 says; left to ticket 15, as this ticket stays out of them.
- `docs/copilot-eval.md`'s Excel section, `docs/agents/standards.md`, `tools/copilot_files.py`'s
  docstring and the code's docstrings naming file 12's T rules or file 20's mark now name 23
  and 24.
- `tests/snapshot/known.txt`: the hashes the new and changed Hive and rows make, added.

### The rounds (2026-11-20, on dev's 20fed6cf, after tickets 18 and 20)

The user: "test it all". Every round's records are in `.eval-local/` (the ledger, `rounds.csv`,
each run folder); 144 proxies, about 5.3 million tokens.

| Round | Haiku | Sonnet |
|---|---|---|
| Excel arm C, dev (62) | 95% (X98, X102, X104) | 98% (X92) |
| Excel arm C, dev, after tuning round 1 | **100%** | not run (held-out tests it) |
| Excel arm C, held-out (62) | **98%** (X111) | **100%** |
| Copilot arm C, dev (36) | 100% | 100% |
| Copilot arm C, held-out (19) | 95% (T54) | 95% (T54) |
| Arm R, the Index, dev (36) | 97% (T52) | - |
| Arm R, the Index, held-out (19) | 100% | - |

**Tuning round 1, files 15 and 20.** Haiku's three dev misses were one gap, which Sonnet named
too: a PivotTable reading a Table a query loads. File 15's P6 and R3 made that Table a step
only when another Table's formula read it, and file 20's PS2 said "FROM what the query loads".
P6 and R3 now say "a PivotTable or another Table's formula", and PS2 "that query's Hive as a
CTE, a step (file 15's P6), never FROM the Table's name". H2's reason was shortened to make
room; file 15 is 8,837 characters. Haiku's dev round then passed all 62.

**X69, held-out, a reference bug.** Both models failed it first, each "types in the rows of
jobs". Its reference CTE (`COSTS_WITH_BUDGETS`) joined `ops.jobs` for a `job_name` no final
reads: the bloated CTE ticket 17 took out of the docs. Both replies left the join out, as
file 15's H2 says, and the scorer asks for every table the reference reads. The join is gone
from the reference (no reference row changes). Scored again on the same replies, held-out is
Haiku 98% and Sonnet 100%.

**T54, held-out, file 22.** Both models answered "batch" and its Hivevar tag in one decisions
cell; `write_decisions` refuses the tag, as it isn't a Decision until "batch" is written. F4
said "Once "batch" is written" but not that the tag waits for it. F4 now says: answer "batch"
alone, with no tag, then accept the proposal in a second decisions cell. Asked again, T54
passes on both, **but that re-ask isn't blind**: the held-out score is the 95% above. The dev
tasks loading file 22 (T51, T52) still pass on both.

**Misses left.** Haiku's X111 (a Bottom 2 value filter on status left unmarked, its rows off)
and dev's X92 on Sonnet (a calculated item's total not named), each one model once. T52 on arm
R routed to file 13, where the Index's P20 names 22.

**From the whole suite, not the rounds.** `docs/main/example_projects.html` showed "No module
named 'warehouse'" in the archived `admin/removed/.../mart__teams_pivot.ipynb`: run there, its
first cell's "two up" is admin/, not the Project. Under pytest a test before it had imported
`warehouse`, so `test_the_committed_page_is_what_the_tool_writes` passed or failed by worker.
`tools/example_projects_page.py` now shows a notebook in admin/removed/ unrun, with a line
saying why (`ARCHIVED`, `is_archived`). `tests/hive_corpus/sqlglot_composer.txt` was written
again after ticket 17's `unchecked_derived` docstring (`COUNT(DISTINCT steps.run_id)`), and a
whole-suite `SNAPSHOT_WRITE=1` run took the 174 hashes of 8.8's texts out of
`tests/snapshot/known.txt` and added ticket 17's 3.

**The reviews (Sonnet) and the beginner reader (Opus), on this section's changes.**

- Standards: `workbook_pivot_hive.py`'s docstring still gave the old PS2; it now says file
  20's words. `is_archived` reads `path.startswith("admin/removed/")`, the plain form.
  `notebook_html`'s `not_run` parameter, for one caller, is kept: a second renderer would
  repeat the loop.
- Spec: this section didn't name the page, corpus and snapshot fixes; it does now.
- Beginner reader ([its report](../reports/beginner-reader-2026-11-20-ticket-14.md)), three
  stops fixed. F4's "a second decisions cell" was untrue: check()
  prints a DECISIONS to paste over the cell's own, so F4 says that, and "keep the proposal to
  accept it". P2 and R3 didn't count a PivotTable as a reader of a formula Table, though the
  code (`piece_roles`: "a step if another piece reads it") does, and X122's reference has no
  `job_runs` final: P2 names a PivotTable, and R3 says "any other piece" in both clauses. PS2
  names its CTE for the query. Not changed: H2's reason (file 15 is at 8,839 of 9,000), the
  archived copy's line not naming the new table, and F4's "the first value kept".
- **These rewordings of files 15, 20 and 22 came after the rounds**: no round has asked them.
  Every Excel task loads file 15, so the next Excel round asks all of them again.

### Round 3 (2026-11-20, on c6d97258): the reviews' rewordings of files 15, 20 and 22

The user: "run 15, 20, and 22 through an eval round". Every Excel task (124, both splits) and
the three tasks loading file 22 (T51, T52, T54), on Haiku and Sonnet: 55 proxies, about 2.9
million tokens. One Haiku proxy (c-17) stopped reading its message at line 576 of 824 and
answered one task of five; it was asked again, and both runs are in the ledger.

| Round | Haiku | Sonnet |
|---|---|---|
| Excel, dev (62) | 95% (X67, X71, X92) | 98% (X92) |
| Excel, held-out (62), not blind | 97% (X30, X120) | 95% (X30, X115, X120) |
| Copilot file 22, T51, T52, T54 | 2 of 3 (T54) | 3 of 3 |

- **X30, on both: R3's new words did it.** X30's PivotTable is only a line, "Also in the
  workbook: a PivotTable on sheet "Pivot", from Table scheduler_runs", which
  `tools/formula_workbook.py` writes for a pivot left alone; its reference keeps
  scheduler_runs a final. R3's "any other piece reads it (a Table, query or PivotTable)" made
  both models call scheduler_runs a step. Before round 3 both passed it. The reader 8.9 ships
  never writes that line, so X30 tests a workbook 8.9 can't give: the task, or R3, wants a
  decision.
- **T54 on Haiku: F4's new words.** Haiku answered "batch" alone, as F4 says, then answered
  the Hivevar too, in a second decisions cell, before check() had printed it, so its Table
  reference differs from the reference's.
- **X115 on Sonnet: file 20's PX6, unchanged since round 1.** "Grouped by seconds, minutes,
  hours, days of several; other bins: no final" was read as refusing a number bin (By 20),
  which PR4 converts. Sonnet passed it in round 1's held-out.
- **The rest, one model each:** X67 and X71 (Haiku), and X92 and X120, a calculated item's
  total not named "added into the total" (both, as in round 1).

**Settled (the user: "Fix X30 and F4").** X30's task no longer has the note-only PivotTable,
its `ignored_pivot` tag or the pivot it asked to be named left alone: a real 8.9 PivotTable
reading scheduler_runs would make it a step and leave the OFFSET and RANDBETWEEN refusals the
task tests in no final, and 8.9's reader never writes the note. X14 (dev) and X40 (held-out)
keep `ignored_pivot`, each pivot's Table a step there anyway. F4 now says to reply with the
"batch" cell alone, no tag in any cell, the proposal coming once it runs. Asked again, X30
and T54 pass on Haiku and Sonnet (not blind).

**Still to do.** The manual round, in Copilot on workbooks the user saves in Excel, waits on
the user, as does ticket 19's fixture repair.

### The manual round (2026-11-20, on cd07280b, files ab03cdcd): Copilot's web chat

The user: "Yes, run it", then "Can we use copilot directly for testing instead of simulating
it in Haiku?". Seven held-out tasks, arm C, in the user's Copilot (copilot.com, model Auto),
driven from the app's browser pane: X25 and X49 (formulas and M), X69 (a Total Row), X107,
X111, X120 and X123 (pivots, X111 and X123 with Pivot filters). Records in
`.eval-local/excel/manual-2026-11-20/`; one ledger row.

- **How the files went in.** As the user loads them: Settings > Personalization > Customize
  Copilot, each task's files from `excel_eval.workbook_files` saved there (24,891 to 36,402
  characters, all taken), one fresh chat per task. Copilot's check refused files 15, 11 and
  12 in that order ("may contain content that violates Microsoft's responsible AI policy")
  and 15 then 11 alone, though each file alone and 11 then 15 passed; saved as 12, 11, 15
  (then 20, 24 or 23 after) every set passed. The pane can't attach a file, so each workbook
  went in as its text, the task's prompt as `excel_eval.py prompts` writes it, which is what
  a proxy reads. Each file, prompt and reply was checked by SHA-256 against the page.
- **Every reply followed file 15's Output**: Map, one block per final, Next; no Toolbox code,
  no invented name.

| Task | Result | Why |
|---|---|---|
| X25, X49, X69, X107 | pass | |
| X111 | FAIL | day_change's base row is 0, not NULL: PV6's "a difference NULL on i's row" skipped; quiet_statuses right, its value filter marked |
| X120 | FAIL | the calculated item `closed` as `SUM(CASE ..) OVER (PARTITION BY job_id)`, PC1's inner SUM dropped; its totals blocks also read `closed_runs` |
| X123 | FAIL, by the scorer (pass once it changed, below) | its final is right; it fails only on the Left alone totals, written as sql blocks reading the pivot's own final `late_alert_share`, which the scorer has no table for (taken out, it passes) |

**4 of 7 (57%), or 5 of 7 reading only the Hive section**, against Haiku's and Sonnet's 97%
and 95% on the same split in round 3 (X120 failed there too, on its mark). Two things this
round can't settle: Copilot's Saved memories and Chat history were on, so its earlier chats
may have reached later ones; and its tokens aren't known (0 in the ledger).

**The scorer changed (the user: "Change the scorer").** A query reading one of the task's
finals by its own name, where no table of the Example database has that name (after
`names`, so X25's `Costs` is still its table), is a total of the final, as file 20's PL2
gives one: `excel_eval.finals_read_by_name` finds it and the scorer leaves it out, unrun; a
reply whose every query is one fails, "reads only its own finals". docs/copilot-eval.md's
pivot section says so. Tests in `tests/test_excel_eval.py`: such a total, bare or as
`<database>.<pivot>`, beside a right reply; a reply of only that; a final that is also a
table (X01's job_runs), and one through `names` (X25's Costs). Scored again on the same
replies: **5 of 7 (71%)**, X123 passing; X111 and X120 fail on their own Hive. The ledger row
keeps the first score. The reviews (Sonnet): Standards, two names a letter apart
(`hive_name`, `database_tables` now) and the doc's wrap; Spec, nothing missing. Its notes,
answered: the skip covers every final, a Total Row's too, which the doc now says; and a query
joining a source to a final by name is left out whole, so a reply that reads a final from the
database where it should work it out still fails, unless another of its queries gives that
final's rows.

**Open, for the user.** Whether X111's and X120's misses, PV6 and PC1 read past by Copilot
and not by the proxies, want a line in file 20.
