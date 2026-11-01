# Usability loop results

One row per scored run (`tools/usability_loop.py score <scenario> <run> --record`).

| date | scenario | split | run | result | questions | note |
|---|---|---|---|---|---|---|
| 2026-11-01 | W1 | dev | 2026-11-01-W1-2 | fail | 0 | Round 1. DONE, but named mart_dev.team_fails with rename= added by hand; key wants mart_dev.team_fails_mart. Scenario's fault: the job names no table. Friction: no rename slot in the convert notebook; README's 'named for the batch' vs <table>_<database>; Run All re-runs convert; compare checks one Partition; do_next and run_workflow disagree after finishing; connection outside the Project needs a sys.path line. |
| 2026-11-01 | W2 | dev | 2026-11-01-W2-1 | pass | 0 | Round 1. DONE. Friction: the message names from_your_team/, absent for W2 (the loop's message); run_notebook.py fails on a relative path; start() and do_next() print nothing from a script; add_references leaves key and does_not_add_up as TODOs, nothing says how to pick a Key. |
| 2026-11-01 | W2 | dev | 2026-11-01-W2-3 | pass | 0 | Round 1. DONE. Friction: from_your_team/ absent (the loop's message); run_notebook.py fails on a relative path; team_connection.py puts main/ first on sys.path (the loop's); Project actions refuse outside the Project folder; warehouse.py's docstring stale once conn is set; check_key refuses until a Key is filled in. |
| 2026-11-01 | W3 | dev | 2026-11-01-W3-1 | pass | 0 | Round 1. DONE. Friction: README's new_table step omits Table references first; the Table notebook and checklist.md send Decisions to convert.ipynb, not new_table's cell (bug); do_next from another Workflow's folder fails on a relative .hql; batch.md names default.failed_runs (bug); check_key on a missing table raises a raw KeyError; connection outside the Project unshown; CONVERSION mark says not what to check. |
| 2026-11-01 | W2 | dev | 2026-11-01-W2-2 | pass | 0 | Round 1. DONE. Friction: run_notebook.py relative path (loop's); from_your_team/ absent (loop's); notebooks edited as JSON without Jupyter; how_to.html 1 MB, no text version; create_table's no-location refusal says edit Table(...) where new_table makes it a Decision; does_not_add_up TODO left for a count. |
| 2026-11-01 | W3 | dev | 2026-11-01-W3-3 | pass | 0 | Round 1. DONE. Friction: run_notebook.py needs PYTHONPATH and an absolute path (loop's); team_connection import and main/ first on sys.path (loop's); notebooks edited as JSON; check_table_reference 'differs' as the loop's DESCRIBE FORMATTED gives no Location (loop's). |
| 2026-11-01 | W1 | dev | 2026-11-01-W1-1 | fail | 0 | Round 1. DONE, but named mart_dev.team_fails with rename= added by hand; key wants team_fails_mart. Scenario's fault, as W1-2. Friction: no rename slot, default <table>_<database> unsaid; no way to run one step without Jupyter; compare checks one Partition; connection import from a subfolder Project. |
| 2026-11-01 | W3 | dev | 2026-11-01-W3-2 | pass | 0 | Round 1. DONE. Friction: run_notebook.py sys.path and relative path (loop's); whole-notebook runs only; QUERIES go through convert, unsaid; Table notebook header sends Decisions to convert.ipynb (bug, as W3-1); new_table leaves the Reference sheet unrefreshed (bug?); DESCRIBE gives no Location (loop's). |
| 2026-11-01 | W1 | dev | 2026-11-01-W1-3 | fail | 0 | Round 1. DONE, but renamed to mart_dev.team_fails by hand, as W1-1 and W1-2; key wants team_fails_mart. Scenario's fault. Friction: no step-at-a-time runner without Jupyter; no rename slot; compare checks one Partition; connection above the Project. |
| 2026-11-01 | W5 | dev | 2026-11-01-W5-1 | pass | 0 | Round 1. DONE. my_project arrived without its sqlglot_composer folder (the loop's: bring_in_the_project copies none); the notebook's import lacks equals; run_workflow would resend the drop; write()'s READS would bring the day back. |
| 2026-11-01 | W4 | dev | 2026-11-01-W4-2 | pass | 0 | Round 1. DONE. Friction: the references Workflow says every step is done with key=None and TODOs left, never asking for the Key (gap: the user's job named the Keys, so the Workflow's DECISIONS key was the way); run_notebook.py relative path (loop's); team_connection import from a plain run (loop's). |
| 2026-11-01 | W5 | dev | 2026-11-01-W5-2 | pass | 0 | Round 1. DONE. my_project lacked sqlglot_composer/ (loop's); change_a_saved_table's import lacks equals and its step names only where=...; condition syntax only in help(); whole-notebook runner; write()'s READS would bring the day back. |
| 2026-11-01 | W5 | dev | 2026-11-01-W5-3 | pass | 0 | Round 1. DONE. my_project lacked sqlglot_composer/ (loop's); equals missing from the notebook's import; run_notebook.py relative path (loop's); READS would bring the day back. |
| 2026-11-01 | W4 | dev | 2026-11-01-W4-3 | pass | 0 | Round 1. DONE, Keys through the decisions cell. Friction: run_notebook.py relative path and sys.path (loop's); whole-notebook runner; connection outside the Project; the job's folder rule names no location for others' tables (scenario's wording); a docstring edit asks a Reference sheet refresh. Read _loop/warehouse.json (empty). |
| 2026-11-01 | W4 | dev | 2026-11-01-W4-1 | pass | 0 | Round 1. DONE. Friction: the references notebook's step 1 stops with SkippedTables once the references exist, no way past but run_workflow (bug?); the team warehouse's refusal names the Example database (loop's stand-in); names cell edited as JSON; refresh_reference_sheet printed twice once; the job's folder rule (scenario's wording). |
| 2026-11-01 | H2 | held_out | 2026-11-01-H2-1 | pass | 0 | Round 1. Held out. Reached the end (upgraded, databases set), then ended on a QUESTION: whether to move the 8.0 Project's mart.* tables to mart_dev and change their locations, as the job's folder rule seemed to ask (scenario's wording; not relayed). Friction: from_your_team/ absent (loop's); SHOW refused with an Example-database message (loop's). |
| 2026-11-01 | H1 | held_out | 2026-11-01-H1-1 | fail | 0 | Round 1. Held out. DONE, every step, but the tables renamed to the originals' names (team_fails etc.) with rename= from a script; key wants team_fails_mart etc. Scenario's fault, as W1. Friction: no rename slot; compare checks one Partition unsaid; ORC default unsaid; promote's dry run asks for locations already filled; run_notebook.py sys.path (loop's). |
| 2026-11-01 | E1 | dev | 2026-11-01-E1-1 | pass | 1 | Round 1. DONE, 1 question. Toolbox bug: convert turns SUM(CASE WHEN c THEN 1 END) into sum_of(1, where=...), which the Toolbox refuses; fixed by hand. The load limit refused an unbounded read, unsaid in the Excel path (Copilot's code had the opt-out, convert's not). run_notebook.py sys.path, SELECT 1 refused (loop's). |
| 2026-11-01 | E2 | dev | 2026-11-01-E2-1 | pass | 1 | Round 1. DONE, 1 question. Copilot's Hive keeps web with a literal team list. Friction: Run All on convert writes before Decisions (ran cells by hand); run_notebook.py (loop's). |
| 2026-11-01 | E2 | dev | 2026-11-01-E2-2 | pass | 1 | Round 1. DONE, 1 question. Its question attached nothing, though the relay attached the workbook (loop's: the message must say how to attach). create refused with no location= before the Decision; re-running convert.ipynb redoes the convert call. |
| 2026-11-01 | E1 | dev | 2026-11-01-E1-2 | pass | 1 | Round 1. DONE, 1 question. Copilot wrote COUNT(CASE ...), so convert didn't hit the sum_of(1) bug. Friction: run_notebook.py (loop's); the question can't attach (loop's message); check_table_reference 'differs' on no Location (loop's warehouse); what a bare SELECT file becomes, unsaid; SHOW DATABASES refused (loop's). |
| 2026-11-01 | E1 | dev | 2026-11-01-E1-3 | pass | 1 | Round 1. DONE, 1 question. Hit the convert bug (sum_of(1, where=...) refused), fixed by hand, as E1-1; the load limit on an unbounded read, opt-out added by hand. |
| 2026-11-01 | E2 | dev | 2026-11-01-E2-3 | pass | 1 | Round 1. DONE, 1 question. The conversion kept Copilot's Hive as an Unchecked statement, its COUNT and SUM types guessed string (answered by hand); Copilot's answer said DEV is ops (wrong); Run All writes before the Decisions. |
| 2026-11-01 | E3 | dev | 2026-11-01-E3-2 | pass | 1 | Round 1. DONE, 1 question. Copilot gave WITH ROLLUP for the Total Row (file 12's rule); the converter took it out by judgement. Friction: check()/do_next hide an open Key after a done step (bug?); file 12 says not that the Total Row lands as data; batch.md names default.daily_runs (bug). |
| 2026-11-01 | E3 | dev | 2026-11-01-E3-3 | pass | 1 | Round 1. DONE, 1 question. Copilot gave WITH ROLLUP (file 12's rule); the Toolbox refused rollup rows in a Saved table, and the converter removed it, restarting its Project. Gap: file 12 maps a Total Row to WITH ROLLUP without saying a Saved table refuses it. |
| 2026-11-01 | E4 | held_out | 2026-11-01-E4-1 | pass | 1 | Round 1. Held out. DONE, 1 question. Phase 1 rebuilt the team's wrong Team runs formula (the scenario's own bug) to its note's meaning. The key guard refused the write as ops.jobs had no Key, and its message doesn't name declaring one as the fix; run_notebook.py sys.path (loop's). |
| 2026-11-01 | E3 | dev | 2026-11-01-E3-1 | pass | 1 | Round 1. Its question went unrelayed at first (the loop's fault), so it waited; once relayed, it wrote daily_runs, its Total Row left out after the Toolbox's refusal of WITH ROLLUP. |

## Round one, 2026-11-01: main's docs as they ship

Main's tree built from 01df34c (8.1's docs with ticket 01's export_hive in). Every dev scenario
three times, every held-out once, fresh Haiku agents for each phase; Copilot's two hops on Haiku
copilot-proxy agents. Nothing was fixed during the round.

| scenario | split | passed | questions | where failed runs stopped |
|---|---|---|---|---|
| W1 | dev | 0/3 | 0 | each did the whole job, renaming the copy mart_dev.team_fails with rename= added to the convert cell by hand; the key holds the Toolbox's name, team_fails_mart |
| W2 | dev | 3/3 | 0 | |
| W3 | dev | 3/3 | 0 | |
| W4 | dev | 3/3 | 0 | |
| W5 | dev | 3/3 | 0 | |
| E1 | dev | 3/3 | 1 each | |
| E2 | dev | 3/3 | 1 each | |
| E3 | dev | 3/3 | 1 each | E3-1's question was relayed late, the loop's fault; it passed once answered |
| H1 | held out | 0/1 | 0 | the whole job done, tables renamed to the originals' names, as W1 |
| H2 | held out | 1/1 | 0 (one asked, not relayed: the end was reached) | |
| E4 | held out | 1/1 | 1 | |

Questions asked: each Excel converter asked Copilot once, for the conversion step 12 names; no
technical user asked. Phase 1 (the non-technical user) asked none in any Excel run.

### Each failure and finding, sorted

**The scenario's own fault**
- W1, H1: the job names no table, and every agent named its copy as the original, by hand; the
  key holds only the Toolbox's default name. (W1-1, W1-2, W1-3, H1-1)
- E4: the presentation workbook's Team runs formula is wrong: COUNTIFS on the SUMPRODUCT of a
  team's job ids, so finance (jobs 2 and 3) counts job 5's runs, 0; the key says 5. (E4-1)
- W4, H2: "Each table's folder is /data/team/<db>.db/<name>" read as asking for locations on
  tables someone else owns (W4-1, W4-3) and as asking to move the 8.0 Project's mart tables
  (H2-1).

**The loop's fault** (the harness, not what main ships)
- The phase message names from_your_team/ when none was given (W2, W5, H2).
- run_notebook.py: a relative path fails (it resolves after its chdir), and it doesn't put the
  notebook's folder on sys.path as a kernel does (nearly every run).
- team_connection.py puts main/ first on sys.path, and sits outside the Project, so a Project
  in a subfolder can't import it without a sys.path line (W1, W2, W3, W4, H1).
- my_project, built from W2's end, holds no sqlglot_composer/ folder (W5-1, W5-2, W5-3).
- The warehouse's refusals name "The Example database", it runs no SHOW DATABASES or
  SELECT 1, and its DESCRIBE FORMATTED gives no Location (W3, W4, E1, E4).
- A question can't say what it attaches, so converters described the workbook, and the relay
  attached it anyway (E1-2, E1-3, E2-2, E4-1).

**Toolbox bugs**
- Converting SUM(CASE WHEN c THEN 1 END) stops on its own refusal, "sum_of(1) was given 1
  where a column goes"; the converter mends it by hand to count_rows(where=...) (E1-1, E1-3).
- A new_table table's notebook header and checklist.md send its Decisions to convert.ipynb's
  decisions cell, not new_table's (W3-1, W3-2).
- batch.md lists a new_table or Excel query's table as default.<name> (W3-1, E3-2), and
  scan.md says a bare SELECT has "its INSERT OVERWRITE" (E2-2).
- project.check() and do_next say every step is done while a Key is still None (E3-2, W4-2).

**Doc gaps** (what a user reads didn't say it)
- The convert notebook has no rename slot, and nothing says the default name is
  <table>_<database> (W1, H1).
- Copilot file 12 maps a Total Row to WITH ROLLUP without saying a Saved table refuses
  subtotal rows: two converters took it out by judgement, one after the refusal (E3-2, E3-3).
- The Steps sheet: step 5 says "a SUMIFS column for each figure" for counts and averages
  too; step 4 shows [@col] where a file written by code holds Table[[#This Row],[col]]; step 2
  says not whether a Table's name keeps its database (E1, E2, E4).
- compare_batch passes on the latest Partition both hold, and its report doesn't say the
  others went unchecked: most converters checked them by hand (W1, H1).
- Run All on a Workflow notebook runs its writes before its Decisions are answered; the README
  says to run each step's cell in turn, but not which cells come before the Decisions (W1, E2).
- The README's new_table section doesn't say the source tables need Table references first
  (W3-1); nothing says how to pick a Key (W2-1).
- change_a_saved_table's notebook imports no equals and its step names only where=... (W5).
- The key guard's refusal on a source with no Key doesn't name declaring one (E4-1); promote's
  dry run asks for prod locations already filled from dev (H1-1); create_table's no-location
  refusal says to edit Table(...) where new_table answers it as a Decision (W2-2).
