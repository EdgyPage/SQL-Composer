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
| 2026-11-01 | W1 | dev | 2026-11-01-r2-W1-2 | pass | 0 | Round 2. RENAME used from the names cell; ran cells by hand to stop at the decision (the runner runs them all); compared the second Partition with partition=. |
| 2026-11-01 | W2 | dev | 2026-11-01-r2-W2-3 | pass | 0 | Round 2. Done through new_table's run_workflow; SELECT 1 refused by the warehouse (the loop's). |
| 2026-11-01 | W2 | dev | 2026-11-01-r2-W2-2 | pass | 0 | Round 2. Done; ran chosen cells by hand (the runner runs every cell, run_workflow too). |
| 2026-11-01 | W1 | dev | 2026-11-01-r2-W1-3 | pass | 0 | Round 2. RENAME used; cells run by hand to stop at the decision. |
| 2026-11-01 | W3 | dev | 2026-11-01-r2-W3-3 | pass | 0 | Round 2. Done; references first, as the README now says. |
| 2026-11-01 | W1 | dev | 2026-11-01-r2-W1-1 | pass | 0 | Round 2. Done with RENAME and run_workflow; a references DECISIONS filled after a run went unwritten until write_decisions by hand (to check). |
| 2026-11-01 | W3 | dev | 2026-11-01-r2-W3-2 | pass | 0 | Round 2. Done; the no-reference refusal sent it to the references Workflow first. |
| 2026-11-01 | W3 | dev | 2026-11-01-r2-W3-1 | pass | 0 | Round 2. Done; unsure whether a query file is new_table's or convert's. |
| 2026-11-01 | W4 | dev | 2026-11-01-r2-W4-1 | pass | 0 | Round 2. Done; SELECT 1 refused (the loop's). |
| 2026-11-01 | W2 | dev | 2026-11-01-r2-W2-1 | pass | 0 | Round 2. Done; DESCRIBE FORMATTED lists no Location, so check_table_reference reports storage unchecked (the loop's). |
| 2026-11-01 | W5 | dev | 2026-11-01-r2-W5-3 | pass | 0 | Round 2. Done; equals from the step cell's import and example. |
| 2026-11-01 | W5 | dev | 2026-11-01-r2-W5-1 | pass | 0 | Round 2. Done; ran the first cells by hand (the runner runs them all). |
| 2026-11-01 | W4 | dev | 2026-11-01-r2-W4-2 | pass | 0 | Round 2. Done through the decisions cell, the Key named open by check(). |
| 2026-11-01 | W5 | dev | 2026-11-01-r2-W5-2 | pass | 0 | Round 2. Done; cells run one at a time. |
| 2026-11-01 | W4 | dev | 2026-11-01-r2-W4-3 | pass | 0 | Round 2. Done; a report shows only when printed from a script. |
| 2026-11-01 | E1 | dev | 2026-11-01-r2-E1-1 | pass | 1 | Round 2. 1 question; through the convert Workflow. |
| 2026-11-01 | E1 | dev | 2026-11-01-r2-E1-3 | pass | 1 | Round 2. 1 question; through new_table's QUERIES. |
| 2026-11-01 | E2 | dev | 2026-11-01-r2-E2-3 | pass | 1 | Round 2. 1 question; Hive kept whole for the typed team list, its columns now typed. |
| 2026-11-01 | E2 | dev | 2026-11-01-r2-E2-1 | pass | 1 | Round 2. 1 question; the key guard refused a key over the CTE of typed team names (unchecked_derived), opted out with unproven_key=True. |
| 2026-11-01 | E2 | dev | 2026-11-01-r2-E2-2 | pass | 1 | Round 2. 1 question; the key guard refused over the literal team list again, mended with key= on the Derived table; promoted too, unasked. |
| 2026-11-01 | E1 | dev | 2026-11-01-r2-E1-2 | pass | 1 | Round 2. 1 question (relayed late: its own background shell hung). |
| 2026-11-01 | E3 | dev | 2026-11-01-r2-E3-1 | pass | 1 | Round 2. 1 question; Copilot gave the Total Row its own query, as file 12 now says; no WITH ROLLUP. |
| 2026-11-01 | E3 | dev | 2026-11-01-r2-E3-2 | pass | 1 | Round 2. 1 question; no ROLLUP, the Total Row its own query. |
| 2026-11-01 | E3 | dev | 2026-11-01-r2-E3-3 | pass | 1 | Round 2. 1 question; no ROLLUP. |

## Round two, 2026-11-01: after ticket 05's fixes and tickets 10 to 14

Main's tree built from f48a70ad: round one's doc, loop and scenario fixes, tickets 10 to 14 in.
Every dev scenario three times, fresh Haiku agents for each phase, Copilot's two hops on Haiku.
Nothing was fixed during the round.

| scenario | split | passed | questions | round one |
|---|---|---|---|---|
| W1 | dev | 3/3 | 0 | 0/3 (named its copy by hand) |
| W2 | dev | 3/3 | 0 | 3/3 |
| W3 | dev | 3/3 | 0 | 3/3 |
| W4 | dev | 3/3 | 0 | 3/3 |
| W5 | dev | 3/3 | 0 | 3/3 |
| E1 | dev | 3/3 | 1 each | 3/3 |
| E2 | dev | 3/3 | 1 each | 3/3 |
| E3 | dev | 3/3 | 1 each | 3/3 (two hit the ROLLUP refusal) |

What round one's fixes did: W1's converters named their copies through RENAME (3/3, from 0/3);
W5's used the step cell's equals import and example; the E3 users turned the Table's Total Row
on in place of a typed total row, and Copilot gave it a query of its own, so no converter met
the ROLLUP refusal; Copilot's typed team list (E2) now has its columns typed, ticket 13.

### Found in round two, sorted

**Toolbox**
- E2-1, E2-2: Copilot's typed team list as a CTE of literal rows becomes an Unchecked derived
  table with no Key, so a write keyed on team is refused; one opted out (unproven_key=True),
  one named key=["team"] on the derived table.

**The loop's fault**
- run_notebook.py runs every cell, run_workflow's too, so nearly every agent wrote its own
  cell runner to stop at a decision, as the README now says.
- The warehouse refuses SELECT 1 (no FROM) and SHOW CREATE TABLE, and loses a CREATE's
  LOCATION between processes, so DESCRIBE FORMATTED lists none and check_table_reference
  reports storage unchecked (W2-1).
- E1-2's own background command hung, and its relay came late.

**Doc gaps** (one or two runs each)
- A project call's report shows only when printed, so a plain script shows nothing (start(),
  check(), run_workflow; W2-3, W3-3, W4-3, W1-1).
- A Table notebook's header TODO stays once its logic is written (W2-2); does_not_add_up's
  TODO doesn't say [] is an answer (W2-2).
- Which Workflow takes one query file, new_table's or convert's (W3-1); first_look's
  signature (W2-1); check_key needs a Key declared, and where= on a partitioned table (W2-2,
  W3-1); warehouse.py keeps its Example database comment once conn changes (W3-3).
| 2026-11-01 | W2 | dev | 2026-11-01-r3-W2-2 | pass | 0 | Round 3. Done with run_notebook --cells; does_not_add_up's TODO not named by reference_from_logic's message. |
| 2026-11-01 | W3 | dev | 2026-11-01-r3-W3-1 | pass | 0 | Round 3. Done. |
| 2026-11-01 | W3 | dev | 2026-11-01-r3-W3-3 | pass | 0 | Round 3. Done with --cells. |
| 2026-11-01 | W2 | dev | 2026-11-01-r3-W2-1 | pass | 0 | Round 3. Done; --cells needs the imports cell first. |
| 2026-11-01 | W2 | dev | 2026-11-01-r3-W2-3 | pass | 0 | Round 3. Done; the DDL's PRIMARY KEY names dt, a partition column (to check). |
| 2026-11-01 | W1 | dev | 2026-11-01-r3-W1-1 | pass | 0 | Round 3. Done with RENAME; both Partitions compared. |
| 2026-11-01 | W1 | dev | 2026-11-01-r3-W1-3 | pass | 0 | Round 3. Done with RENAME. |
| 2026-11-01 | W1 | dev | 2026-11-01-r3-W1-2 | pass | 0 | Round 3. Done with RENAME. |
| 2026-11-01 | W3 | dev | 2026-11-01-r3-W3-2 | pass | 0 | Round 3. Done. |
| 2026-11-01 | W4 | dev | 2026-11-01-r3-W4-1 | pass | 0 | Round 3. Done. |
| 2026-11-01 | W4 | dev | 2026-11-01-r3-W4-3 | pass | 0 | Round 3. Done. |
| 2026-11-01 | W5 | dev | 2026-11-01-r3-W5-1 | pass | 0 | Round 3. Done with --cells. |
| 2026-11-01 | W5 | dev | 2026-11-01-r3-W5-3 | pass | 0 | Round 3. Done. |
| 2026-11-01 | W5 | dev | 2026-11-01-r3-W5-2 | pass | 0 | Round 3. Done. |
| 2026-11-01 | W4 | dev | 2026-11-01-r3-W4-2 | pass | 0 | Round 3. Done. |
| 2026-11-01 | E1 | dev | 2026-11-01-r3-E1-1 | pass | 1 | Round 3. 1 question; caught Copilot's wrong <database> (it said Dev) from the sheet's ops note. |
| 2026-11-01 | E1 | dev | 2026-11-01-r3-E1-2 | pass | 1 | Round 3. 1 question. |
| 2026-11-01 | E1 | dev | 2026-11-01-r3-E1-3 | pass | 1 | Round 3. 1 question. |
| 2026-11-01 | E2 | dev | 2026-11-01-r3-E2-1 | pass | 1 | Round 3. 1 question; no key opt-out needed for the typed team list. |
| 2026-11-01 | E2 | dev | 2026-11-01-r3-E2-3 | pass | 1 | Round 3. 1 question. |
| 2026-11-01 | E2 | dev | 2026-11-01-r3-E2-2 | pass | 1 | Round 3. 1 question; Copilot read the teams from jobs, not the typed list (a team only typed in would drop). |
| 2026-11-01 | E3 | dev | 2026-11-01-r3-E3-2 | pass | 1 | Round 3. 1 question; the Total Row its own query, no ROLLUP. |
| 2026-11-01 | E3 | dev | 2026-11-01-r3-E3-1 | pass | 1 | Round 3. 1 question; went through new_table's QUERIES, reading convert as needing a script that writes a table (it takes a query alone too). |
| 2026-11-01 | E3 | dev | 2026-11-01-r3-E3-3 | pass | 1 | Round 3. 1 question; Copilot misread the real Total Row as typed, the converter checked it. |

## Round three, 2026-11-01: after ticket 15 and round two's harness fixes

Main's tree built from de23a133. Every dev scenario three times, fresh Haiku agents, Copilot's
two hops on Haiku. Nothing was fixed during the round.

| scenario | split | passed | questions |
|---|---|---|---|
| W1 | dev | 3/3 | 0 |
| W2 | dev | 3/3 | 0 |
| W3 | dev | 3/3 | 0 |
| W4 | dev | 3/3 | 0 |
| W5 | dev | 3/3 | 0 |
| E1 | dev | 3/3 | 1 each |
| E2 | dev | 3/3 | 1 each |
| E3 | dev | 3/3 | 1 each |

Two rounds running with every dev scenario at 3/3: ticket 05 is done. The agents ran each
Workflow's cells with run_notebook.py --cells, stopping at each decision; no E2 run needed a
key opt-out over a list of teams typed in; no E3 run met the ROLLUP refusal.

### Found in round three, for after 8.2's raise (none failed a run)

**Copilot files**
- File 11 says not how a summary keeps the groups its rows list with no data (web): two
  answers typed the list in, one read the teams from jobs, which drops a team typed in only
  (E2-2). File 11 has 2 characters to spare: a cut or a file 15.
- A Table's real Total Row was read as a total typed as a row, by a Copilot answer (E3-3) and a
  converter (E3-1): file 11 should say Excel keeps the Total Row inside the Table's range.
- One answer said `<database>` is the Dev Database where the source's note named ops; the
  converter caught it (E1-1).

**Docs**
- `--cells` needs the imports cell with it; how to run a step's Check first line (W5-2).
- Which Workflow takes one query file, new_table's QUERIES or convert's (W3-1, W3-2, E3-1).
- The tables a convert reads need Table references first, unsaid in its section (W1-1, W1-2).
- warehouse.py's docstring says it imports none of your files (W3-3, W1-1).
- reference_from_logic names one TODO line where two are left (W2-2).
- The generated DDL's PRIMARY KEY names a partition column, dt (W2-3): to check against Hive.
| 2026-11-01 | H2 | held_out | 2026-11-01-held-H2-1 | pass | 0 | Held-out, after rounds 2 and 3. Done. |
| 2026-11-01 | H1 | held_out | 2026-11-01-held-H1-1 | pass | 0 | held-out, main bcb2239f; 0 questions; RENAME used as the names cell says; spotted the original's job_id-only join inflating counts and left it as a decision |
| 2026-11-01 | E4 | held_out | 2026-11-01-held-E4-1 | pass | 1 | held-out, main bcb2239f; 1 question (the conversion, file 11 routed); Parameters, the typed-over value and Keys used; both tables right by hand; found: Copilot's typed-in rows in a FROM subquery keep the whole query as Unchecked Hive |

## The held-out round, 2026-11-01: the docs as tuning left them

Main's tree built from bcb2239f: rounds one to three's fixes and tickets 10 to 15 in. Each
held-out scenario once, fresh Haiku agents for each phase, Copilot's two hops on Haiku. Its
three rows are just above; nothing is changed after it for 8.2's docs.

| scenario | split | passed | questions | round one |
|---|---|---|---|---|
| H1 | held out | 1/1 | 0 | 0/1 (named its copies by hand, as W1) |
| H2 | held out | 1/1 | 0 | 1/1 (ended on a question of the job's wording) |
| E4 | held out | 1/1 | 1 | 1/1 (the key guard's message named no fix) |

What tuning did for a job it wasn't tuned on: H1 named its copies as the originals through
RENAME, as the names cell says, with no question, where round one renamed them from a script;
it compared a second Partition by hand once batch.md said the compare checked one, and named the
original's job_id-only join, which counts each failed run once a day of owner rows, as a
decision left to the user. H2 upgraded and set the Databases with no question. E4's converter
asked Copilot once, for the conversion, and each table's rows came out right by hand.

### Found in the held-out round

- E4: Copilot's Hive lists a summary's typed groups as a subquery in FROM, `(SELECT 1 AS
  job_id UNION ALL ...) c`, and convert keeps each such query whole as an Unchecked statement,
  "a SELECT with no FROM": ticket 15 lifts only a CTE of rows typed in. A Toolbox gap, not a
  docs one, so it is ticket 16, fixed for 8.2 without running the round again.
| 2026-11-01 | W5 | dev | 2026-11-01-r18-W5-1 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; Edit refuses .ipynb, filled by a script; checked partitions before and after |
| 2026-11-01 | W5 | dev | 2026-11-01-r18-W5-3 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; found: step 2's Check first gives no call; --cells counts code cells, not steps |
| 2026-11-01 | W5 | dev | 2026-11-01-r18-W5-2 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; found: --cells 4 alone fails (fresh namespace), unsaid in the Workflow text |
| 2026-11-01 | W4 | dev | 2026-11-01-r18-W4-1 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; found: how-to's check_key step doesn't say a partitioned table needs where=; the Workflow's Done when covers the Key, not the other TODO lines |
| 2026-11-01 | W4 | dev | 2026-11-01-r18-W4-3 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; check_key on run_alerts with reads_all_partitions=True where where= would do; found: nothing says how warehouse.py imports a connection outside the Project |
| 2026-11-01 | W1 | dev | 2026-11-01-r18-W1-2 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; RENAME used; second Partition compared by hand; found: the Workflow's compare step covers the latest Partition only and a rerun overwrites compare.md |
| 2026-11-01 | W1 | dev | 2026-11-01-r18-W1-3 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; RENAME used; second Partition compared by hand; found: README's convert section names neither RENAME's default nor the one-Partition compare |
| 2026-11-01 | W4 | dev | 2026-11-01-r18-W4-2 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; found: nothing says how to find a Partition value for check_key (last_n_days(30) found none, 365 did); warehouse.py's docstring says it imports none of your files |
| 2026-11-01 | W3 | dev | 2026-11-01-r18-W3-2 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; new_table with QUERIES; kept the CONVERSION reads_all_partitions; found: check_references prints a check_key call with a literal <a value>; --cells needs 1-3 each time |
| 2026-11-01 | W3 | dev | 2026-11-01-r18-W3-1 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; found: the CONVERSION note stays in project.check() after compare passes; the Key comment still reads as open once accepted; new_table's convert batch folder confuses |
| 2026-11-01 | W3 | dev | 2026-11-01-r18-W3-3 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; wrote a backup to /tmp/x outside its folder and removed it; found: --cells must include the imports and names cells, unsaid; the convert batch moving to finished/ surprised it |
| 2026-11-01 | W1 | dev | 2026-11-01-r18-W1-1 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; RENAME used; second Partition compared by hand; found: README's check_key step has no where= for a partitioned table; compare with partition= overwrites compare.md |
| 2026-11-01 | W2 | dev | 2026-11-01-r18-W2-2 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; found: --cells needs the names cell; reference_from_logic leaves TODO lines step 3 doesn't name; the Table notebook's text cell keeps its TODO wording |
| 2026-11-01 | W2 | dev | 2026-11-01-r18-W2-1 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; Project in my_work itself; found: README says --cells runs as in Jupyter, but the imports cell must be named; the Table notebook's text keeps its Template wording |
| 2026-11-01 | W2 | dev | 2026-11-01-r18-W2-3 | pass | 0 | ticket 18 rerun, main bf383aa; 0 questions; found: Run All of the references notebook after a Decision refuses at add_references (the file is there already) where a step done should be skipped |
| 2026-11-01 | H2 | held_out | 2026-11-01-r18-H2-1 | pass | 0 | held-out, ticket 18 rerun, main bf383aa; 0 questions; upgraded 8.0 to 8.2, export_hive run in each Table notebook; left the existing tables' placeholder locations to the user |
| 2026-11-01 | H1 | held_out | 2026-11-01-r18-H1-1 | pass | 0 | held-out, ticket 18 rerun, main bf383aa; 0 questions; RENAME used, temp table folded, both Partitions compared, promoted; found: warehouse.py's docstring out of date once conn imports a team file |
| 2026-11-01 | E1 | dev | 2026-11-01-r18-E1-1 | pass | 1 | ticket 18 rerun, main bf383aa; 1 question (the conversion; route named 15, 11, 12); NAME sets the table where the file is report.hql |
| 2026-11-01 | E1 | dev | 2026-11-01-r18-E1-3 | pass | 1 | ticket 18 rerun, main bf383aa; 1 question (the conversion); phase 1 took step 12 as its own and stopped there, its question lost, so the converter asked |
| 2026-11-01 | E1 | dev | 2026-11-01-r18-E1-2 | pass | 1 | ticket 18 rerun, main bf383aa; 1 question (the conversion); found: batch.md lists the same CONVERSION note three times |
| 2026-11-01 | E2 | dev | 2026-11-01-r18-E2-3 | pass | 1 | ticket 18 rerun, main bf383aa; 1 question (the conversion); Copilot made job_runs a step with its team a LEFT JOIN into jobs |
| 2026-11-01 | E2 | dev | 2026-11-01-r18-E2-1 | pass | 1 | ticket 18 rerun, main bf383aa; 1 question (the conversion); ran the convert cell twice by mistake, nothing lost |
| 2026-11-01 | E2 | dev | 2026-11-01-r18-E2-2 | pass | 1 | ticket 18 rerun, main bf383aa; 1 question (the conversion); reran the convert cell once, its edits kept |
| 2026-11-01 | E3 | dev | 2026-11-01-r18-E3-1 | pass | 1 | ticket 18 rerun, main bf383aa; 1 question (the conversion); found: Copilot wrote Excel's AND() as IF(AND(a, b), 1, 0), which Hive has no function for; the converter rewrote it as a AND b |
| 2026-11-01 | E4 | held_out | 2026-11-01-r18-E4-1 | pass | 1 | held-out, ticket 18 rerun, main bf383aa; 1 question (the conversion); Parameters, the typed-over value and Keys used; both tables right by hand |
| 2026-11-01 | E3 | dev | 2026-11-01-r18-E3-3 | pass | 1 | ticket 18 rerun, main bf383aa; 1 question (the conversion; answered again once the loop showed the Total Row as one); left the Total Row final out; found: nothing says whether a Total Row final is saved as a table |
| 2026-11-01 | E3 | dev | 2026-11-01-r18-E3-2 | pass | 2 | ticket 18 rerun, main bf383aa; 2 questions, the second only because the loop showed the Total Row as a typed row (fixed in tools/usability_loop.py); took new_table with QUERIES; listed _loop/ once by mistake |

## The ticket 18 round, 2026-11-01: every doc rewritten to Microsoft's instruction rules

Main's tree built from bf383aa, ticket 18's rewrite: Copilot files 00 to 15, the README
template, the how-tos, the Steps sheet and the notebooks' text cells. Every dev scenario three
times and every held-out one once, fresh Haiku agents for each phase, Copilot's two hops on
Haiku, the Excel answer loading files 15, 11 and 12. Nothing in the docs was changed during the
round; the loop's own view of an attached workbook was (below). The 27 rows are just above.

| scenario | split | passed | questions | round three |
|---|---|---|---|---|
| W1 | dev | 3/3 | 0 | 3/3, 0 |
| W2 | dev | 3/3 | 0 | 3/3, 0 |
| W3 | dev | 3/3 | 0 | 3/3, 0 |
| W4 | dev | 3/3 | 0 | 3/3, 0 |
| W5 | dev | 3/3 | 0 | 3/3, 0 |
| E1 | dev | 3/3 | 1 each | 3/3, 1 each |
| E2 | dev | 3/3 | 1 each | 3/3, 1 each |
| E3 | dev | 3/3 | 1, 2, 1 | 3/3, 1 each |
| H1 | held out | 1/1 | 0 | held-out round: 1/1, 0 |
| H2 | held out | 1/1 | 0 | held-out round: 1/1, 0 |
| E4 | held out | 1/1 | 1 | held-out round: 1/1, 1 |

The rewrite kept every scenario passing, its questions the one conversion each Excel run asks
for. E3-2's second question came from the loop, not the docs: `workbook_text` showed an
attached Table's Total Row as one more typed row, so Copilot wrote a `Total` row of NULLs and
the converter asked again. The loop now names each Table row as the Excel evaluation does
(Headers, Row n, Total Row), tested by
`test_an_attached_tables_total_row_is_named_as_the_excel_eval_names_it`; E3-3's answer was made
again with it before reaching its converter. Every Excel route answered files 15, 11 and 12,
though the route message's reply asks for one file (the proxies said so).

### Found in the ticket 18 round, none failing a run

**Copilot files**
- E3-1: Copilot wrote Excel's `AND(a, b)` inside an IF as `IF(AND(a, b), 1, 0)`, which Hive has
  no function for; the converter rewrote it `IF(a AND b, 1, 0)`. File 11 should say AND() and
  OR() become the operators. The convert's refusal ("its Hive writes no table, and holds no
  query alone to save") named the wrong cause.
- E3-2, E3-3: nothing says whether a Total Row's final is saved as a table too; both converters
  left it out, as the job named one table.
- The route message's reply format asks for one file where the Excel path loads three.

**Docs**
- `run_notebook.py --cells` runs each call fresh, so the imports and names cells go with every
  step; the README says "as you would one at a time in Jupyter" (W2-1, W2-2, W3-2, W3-3, W5-2).
- `check_key` on a partitioned table needs `where=`, unsaid in the references how-to's step and
  the README's step 5; `check_references` prints a call with a literal `<a value>` (W1-1, W3-2,
  W4-1, W4-2); one run took `reads_all_partitions=True` instead (W4-3).
- The convert compare checks the latest Partition, and a compare with `partition=` overwrites
  compare.md (W1-1, W1-2, W1-3).
- How warehouse.py imports a connection kept outside the Project, and its docstring saying it
  imports none of your files (W1-1, W4-2, W4-3, H1).
- Running the references notebook top to bottom after answering a Key refuses at
  add_references, "the file is there already", where a step done should be skipped (W2-3).
- A Table notebook's text keeps its Template wording once filled in; a proposed Key's comment
  still reads as open once accepted; the CONVERSION note stays after the compare passes (W2-1,
  W3-1).
- Phase 1 of E1-3 took the Steps sheet's step 12, Copilot, as its own job and stopped there;
  E3-3 found no fallback when a Power Query can't be added; examples 01 and 02 show no source
  line above a Table's header, which step 2 asks for (E1-1, E2-2).
