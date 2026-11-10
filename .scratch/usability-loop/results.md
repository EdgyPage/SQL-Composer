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
| 2026-11-01 | W4 | dev | 2026-11-01-r19-W4-3 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; check_references checked the partitioned Key itself; found: README's step 3 says to fill the Key TODO by hand where the Workflow writes it |
| 2026-11-01 | W4 | dev | 2026-11-01-r19-W4-1 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; used the README's outside-the-Project connection lines and --cells with the imports and names cells, as now said; found: example_database left imported, unused |
| 2026-11-01 | W4 | dev | 2026-11-01-r19-W4-2 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; found: the runner's code-cell numbers differ from the Workflow's step numbers; nothing says how to edit a notebook's cell without Jupyter |
| 2026-11-01 | W1 | dev | 2026-11-01-r19-W1-2 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; RENAME used; compared the second Partition as the compare step now says, both results kept in compare.md |
| 2026-11-01 | W1 | dev | 2026-11-01-r19-W1-1 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; both Partitions compared as the step says; read _loop/warehouse.json once by mistake; found: finished/ before the other Partition is compared reads as every Partition checked |
| 2026-11-01 | W3 | dev | 2026-11-01-r19-W3-1 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; found: new_table step 1 runs a convert batch unsaid; runner cell numbers not shown in the Workflow's headings |
| 2026-11-01 | W2 | dev | 2026-11-01-r19-W2-3 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; found: how to save a notebook's cells without Jupyter unsaid; the TODO count names the docstring, not does_not_add_up |
| 2026-11-01 | W1 | dev | 2026-11-01-r19-W1-3 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; both Partitions compared; named the original's job_id-only join as a decision left to the user |
| 2026-11-01 | W3 | dev | 2026-11-01-r19-W3-2 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; found: new_table's QUERIES runs a convert unsaid; write_decisions' TODO count leaves out the docstring's |
| 2026-11-01 | W5 | dev | 2026-11-01-r19-W5-1 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; the loop broke my_project/warehouse.py (its connection replace hit 8.2's comment quoting conn = example_database), and the agent repaired it from the README's lines; read _loop/ once |
| 2026-11-01 | W5 | dev | 2026-11-01-r19-W5-2 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; repaired the warehouse.py the loop broke, from README step 5 |
| 2026-11-01 | W2 | dev | 2026-11-01-r19-W2-2 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; found: new_table's steps don't say to fill the reference's leftover TODO lines; how to edit a notebook without Jupyter |
| 2026-11-01 | W3 | dev | 2026-11-01-r19-W3-3 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; new_table step 1 refused for a missing Table reference, named the references Workflow, recovered; found: new_table's steps don't say a read table needs its reference first |
| 2026-11-01 | W5 | dev | 2026-11-01-r19-W5-3 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; repaired the warehouse.py the loop broke, from README step 5 |
| 2026-11-01 | W2 | dev | 2026-11-01-r19-W2-1 | pass | 0 | ticket 19 rerun, main b74f1a0; 0 questions; found: the Table notebook's first cell stops on a location not yet answered, unwarned; made and removed files in Temp outside its folder |
| 2026-11-01 | H1 | held_out | 2026-11-01-r19-H1-1 | pass | 0 | ticket 19 rerun, main b74f1a0; held-out; 0 questions; both Partitions compared; promoted |
| 2026-11-01 | E2 | dev | 2026-11-01-r19-E2-1 | pass | 1 | ticket 19 rerun, main b74f1a0; 1 question (the conversion); phase 1 took step 12 as its own |
| 2026-11-01 | E1 | dev | 2026-11-01-r19-E1-1 | pass | 1 | ticket 19 rerun, main b74f1a0; 1 question (the conversion); phase 1 took step 12 as its own; reran the convert cell once, nothing lost |
| 2026-11-01 | H2 | held_out | 2026-11-01-r19-H2-1 | pass | 1 | held-out, ticket 19 rerun, main b74f1a0; 1 question; upgraded 8.0 to 8.2 and set the Databases; then asked whether to rename the mart.* tables to mart_dev.* and, Copilot leaving it open, moved them, beyond its job; warehouse.py the loop broke, repaired |
| 2026-11-01 | E1 | dev | 2026-11-01-r19-E1-3 | pass | 1 | ticket 19 rerun, main b74f1a0; 1 question (the conversion); phase 1 asked Copilot at step 12 itself |
| 2026-11-01 | E2 | dev | 2026-11-01-r19-E2-2 | pass | 1 | ticket 19 rerun, main b74f1a0; 1 question (the conversion); miscounted a --cells number once, refused before any write |
| 2026-11-01 | E1 | dev | 2026-11-01-r19-E1-2 | pass | 1 | ticket 19 rerun, main b74f1a0; 1 question (the conversion); ran the wrong cell number once, refused before sending |
| 2026-11-01 | E2 | dev | 2026-11-01-r19-E2-3 | pass | 1 | ticket 19 rerun, main b74f1a0; 1 question (the conversion) |
| 2026-11-01 | E3 | dev | 2026-11-01-r19-E3-2 | pass | 1 | ticket 19 rerun, main b74f1a0; 1 question (the conversion); phase 1 typed the Power Query's rows in as example 03 shows, Copilot read its M; found: do_next after a finished batch reads as an error |
| 2026-11-01 | E4 | held_out | 2026-11-01-r19-E4-1 | pass | 1 | held-out, ticket 19 rerun, main b74f1a0; 1 question (the conversion); Parameters, the typed-over value and Keys used; both tables right by hand |
| 2026-11-01 | E3 | dev | 2026-11-01-r19-E3-3 | pass | 1 | ticket 19 rerun, main b74f1a0; 1 question (the conversion); phase 1 stopped STUCK at step 7, the Power Query needing Excel; Copilot read the query from its M |
| 2026-11-01 | E3 | dev | 2026-11-01-r19-E3-1 | pass | 1 | ticket 19 rerun, main b74f1a0; 1 question (the conversion); found: nothing says a Total Row final may be left out |

## The ticket 19 round, 2026-11-01: what ticket 18's round found, fixed

Main's tree built from b74f1a0, ticket 19: Excel's AND() and OR() in file 11 and the refusal
for Hive sqlglot can't read, `--cells` said to start with nothing defined, check_references
checking a partitioned Key itself, compare.md keeping each Partition's result, and how
warehouse.py reaches a connection outside the Project. Every dev scenario three times and every
held-out one once, fresh Haiku agents for each phase, Copilot's two hops on Haiku. The 27 rows
are just above.

| scenario | split | passed | questions | the ticket 18 round |
|---|---|---|---|---|
| W1 | dev | 3/3 | 0 | 3/3, 0 |
| W2 | dev | 3/3 | 0 | 3/3, 0 |
| W3 | dev | 3/3 | 0 | 3/3, 0 |
| W4 | dev | 3/3 | 0 | 3/3, 0 |
| W5 | dev | 3/3 | 0 | 3/3, 0 |
| E1 | dev | 3/3 | 1 each | 3/3, 1 each |
| E2 | dev | 3/3 | 1 each | 3/3, 1 each |
| E3 | dev | 3/3 | 1 each | 3/3, 1, 2, 1 |
| H1 | held out | 1/1 | 0 | 1/1, 0 |
| H2 | held out | 1/1 | 1 | 1/1, 0 |
| E4 | held out | 1/1 | 1 | 1/1, 1 |

What the fixes did: every W1 run compared both Partitions and kept both results in
compare.md; W4's check_references checked run_alerts' Key on its latest Partition itself; the
agents ran `--cells` with the imports and names cells; W4-1 and W1-1 reached the team's
connection with the README's new lines. No run met the AND() refusal: Copilot wrote operators.

The loop broke W5's and H2's my_project/warehouse.py: its connect step replaced every
`conn = example_database`, and 8.2's warehouse.py named that line in a comment too. Each agent
repaired it from the README's step 5. Fixed after the round: the comment no longer quotes the
line, and the loop replaces the code line alone (`connect_the_team`, tested).

### Found in the ticket 19 round, none failing a run

- H2 upgraded and set DEV to mart_dev, then asked what becomes of the Project's mart.* tables,
  which promote now refuses; Copilot left it open and the agent moved them to mart_dev.*,
  beyond its job. Nothing says what an Upgrade's Databases mean for tables named before.
- Phase 1 of an Excel run stops at step 12 or at step 7 when it can't add a Power Query
  without Excel (E1-1, E1-3, E2-1, E3-1 to E3-3): the Steps sheet gives no fallback, and its
  step 7 (From Table/Range) and example 03 (Blank Query) differ.
- The runner's code-cell numbers aren't shown beside the Workflow's step headings (W3-1,
  W4-2, H1); editing a notebook's cell without Jupyter is unsaid (W2-2, W2-3, W4-2).
- new_table's QUERIES runs a convert batch unsaid; a read table needs its reference first;
  write_decisions' TODO count leaves out the docstring's (W3-1 to W3-3).
- A Total Row final may be left out, unsaid (E3-1, E3-2); project.do_next() after a finished
  batch reads as an error (E3-2).
| 2026-11-01 | W5 | dev | 2026-11-01-r20-W5-3 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; no cell runs step 2's SHOW PARTITIONS check |
| 2026-11-01 | W5 | dev | 2026-11-01-r20-W5-1 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; no cell runs step 2's SHOW PARTITIONS check |
| 2026-11-01 | W5 | dev | 2026-11-01-r20-W5-2 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; wrote a scratch file outside its folder once, deleted it |
| 2026-11-01 | H2 | held_out | 2026-11-01-r20-H2-1 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; named DEV/PROD, old tables kept their names as the README says |
| 2026-11-01 | W4 | dev | 2026-11-01-r20-W4-1 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; README step 2 stray 'then go on to 3', how-to warehouse.py 'in step 8' |
| 2026-11-01 | W4 | dev | 2026-11-01-r20-W4-2 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; --list before the path printed only the usage |
| 2026-11-01 | W1 | dev | 2026-11-01-r20-W1-3 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; RENAME found in the names cell's comment, not the README; compared the second Partition too |
| 2026-11-01 | W1 | dev | 2026-11-01-r20-W1-1 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; compared the second Partition with partition= |
| 2026-11-01 | W1 | dev | 2026-11-01-r20-W1-2 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; README's single-file batch naming unclear |
| 2026-11-01 | W3 | dev | 2026-11-01-r20-W3-1 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; new_table step 2 'a decision' when logic is written for you |
| 2026-11-01 | W2 | dev | 2026-11-01-r20-W2-3 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; the TODO-lines message names no line |
| 2026-11-01 | W2 | dev | 2026-11-01-r20-W2-2 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; TODO lines and choosing a Key not said in the steps |
| 2026-11-01 | W4 | dev | 2026-11-01-r20-W4-3 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; quotes in a notebook's JSON source lines easy to get wrong |
| 2026-11-01 | W3 | dev | 2026-11-01-r20-W3-2 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; step 3 'kept, it is yours' with TODO lines left |
| 2026-11-01 | W2 | dev | 2026-11-01-r20-W2-1 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; cell numbers only in the runner's help |
| 2026-11-01 | W3 | dev | 2026-11-01-r20-W3-3 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; project.check() doesn't flag a key=None TODO |
| 2026-11-01 | H1 | held_out | 2026-11-01-r20-H1-1 | pass | 0 | ticket 20 rerun, main 7847124; 0 questions; promote's decisions step had nothing to answer |
| 2026-11-01 | E1 | dev | 2026-11-01-r20-E1-3 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions, phase 2 1 (convert); step 12 the data team's |
| 2026-11-01 | E1 | dev | 2026-11-01-r20-E1-2 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions, phase 2 1 (convert) |
| 2026-11-01 | E2 | dev | 2026-11-01-r20-E2-1 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions, phase 2 1 (convert) |
| 2026-11-01 | E2 | dev | 2026-11-01-r20-E2-2 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions, phase 2 1 (convert) |
| 2026-11-01 | E3 | dev | 2026-11-01-r20-E3-1 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions (step 7 fallback used), phase 2 1; Total Row left out as asked |
| 2026-11-01 | E2 | dev | 2026-11-01-r20-E2-3 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions, phase 2 1 (convert); one turn ended early, resumed |
| 2026-11-01 | E3 | dev | 2026-11-01-r20-E3-2 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions (step 7 fallback used), phase 2 1; left out the Total Row's query, as the README says |
| 2026-11-01 | E4 | held_out | 2026-11-01-r20-E4-1 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions, phase 2 1 (convert) |
| 2026-11-01 | E3 | dev | 2026-11-01-r20-E3-3 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions (step 7 fallback), phase 2 1; Total Row's query left out; my relay was slow |
| 2026-11-01 | E1 | dev | 2026-11-01-r20-E1-1 | pass | 1 | ticket 20 rerun, main 7847124; phase 1 0 questions, phase 2 1 (convert); a probe of its own hung, resumed in the foreground |

## The ticket 20 round, 2026-11-01: what ticket 19's round found, fixed

Main's tree was built from 7847124, which holds ticket 20's changes:
- the Steps sheet's step 7 adds a query from its M, with a fallback for an Excel that can't
  add one, and step 12 may be the data team's;
- the README leaves out a final no one needs, such as a Total Row, and says naming DEV and
  PROD renames nothing;
- new_table's step 1 names the Table references a query needs first;
- write_decisions counts a docstring's TODO line, and do_next() says each Workflow started is
  done;
- file 12 leaves out a Total Row no one needs;
- the runner gained `--list`.

Each dev scenario ran three times and each held-out one once, with fresh Haiku agents for each
phase and both Copilot steps on Haiku. The 27 rows are just above.

| scenario | split | passed | questions | the ticket 19 round |
|---|---|---|---|---|
| W1 | dev | 3/3 | 0 | 3/3, 0 |
| W2 | dev | 3/3 | 0 | 3/3, 0 |
| W3 | dev | 3/3 | 0 | 3/3, 0 |
| W4 | dev | 3/3 | 0 | 3/3, 0 |
| W5 | dev | 3/3 | 0 | 3/3, 0 |
| E1 | dev | 3/3 | 1 each, the convert | 3/3, 1 each |
| E2 | dev | 3/3 | 1 each, the convert | 3/3, 1 each |
| E3 | dev | 3/3 | 1 each, the convert | 3/3, 1 each |
| H1 | held out | 1/1 | 0 | 1/1, 0 |
| H2 | held out | 1/1 | 0 | 1/1, 1 |
| E4 | held out | 1/1 | 1, the convert | 1/1, 1 |

What the fixes did:
- Excel phase 1 asked nothing: each run stopped at step 12, now the data team's. Each phase 2
  asked one question, the convert itself, as step 12 says.
- E3's three runs used step 7's fallback: the M sat under `Query CleanRuns:` on the Power
  Query sheet, with its rows typed into a Table of its name. Copilot read the M.
- Total Rows were left out. E3-1 asked for that and Copilot did so; E3-2 and E3-3 dropped the
  Total Row's query, as README step 5 says.
- H2 named DEV and PROD and kept the old mart.* names, as the README says; it asked nothing.

Two runs needed a nudge, and neither was a docs failure:
- E2-3 ended a turn early.
- E1-1 waited on a hung probe of its own.

E3-3 asked three times before my relay answered it.

### Found in the ticket 20 round, none failing a run

- **TODO lines (W2-1 to W2-3, W3-2, W3-3).** "N TODO lines left ... wait on nothing" names no
  line. new_table's step 3 says "Kept ...: it is yours" and leaves them. The steps don't say to
  fill them. W3-3 also saw project.check() not flag a source reference's `key=None` TODO.
- **change_a_saved_table step 2 (W5-1, W5-3).** It says to run the check its Check first line
  names (SHOW PARTITIONS), but no cell runs it, and the README's chart calls the step "only
  prints".
- **The runner (W4-2, W3-1).** `--list` before the path prints only the usage line.
- **The convert Workflow (W1-2, W1-3).** The README's naming of a one-file batch reads as
  unclear, and RENAME is said only in the names cell's comment.
- **new_table (W3-1, W2-2).** Step 2 calls it a decision when QUERIES wrote the logic. The
  logic text of a table with no query says its Key is "proposed from its query".
- **promote (H1).** Its decisions step had nothing to answer, since promote fills `location=`,
  but it reads as if something must be answered.
- **The README (W4-1).** Its seven "then go on to N. <Section>" endings read as a stray
  sentence.
| 2026-11-01 | W5 | dev | 2026-11-01-r21-W5-3 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; step 2's cell ran the SHOW PARTITIONS check itself |
| 2026-11-01 | W5 | dev | 2026-11-01-r21-W5-2 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; step 2's cell ran the check |
| 2026-11-01 | W5 | dev | 2026-11-01-r21-W5-1 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; project.check() refuses outside the Project, clearly |
| 2026-11-01 | W4 | dev | 2026-11-01-r21-W4-2 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; a pending sheet refresh not said why |
| 2026-11-01 | W4 | dev | 2026-11-01-r21-W4-1 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; Workflow step doesn't say deleting does_not_add_up's TODO means none (README does) |
| 2026-11-01 | H2 | held_out | 2026-11-01-r21-H2-1 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; named DEV/PROD, old tables kept their names |
| 2026-11-01 | W3 | dev | 2026-11-01-r21-W3-2 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; used the convert Workflow; check()'s Done-when line missing after convert |
| 2026-11-01 | W4 | dev | 2026-11-01-r21-W4-3 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; check_key's where= refusal clear |
| 2026-11-01 | W1 | dev | 2026-11-01-r21-W1-3 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; RENAME from the README; compared both Partitions |
| 2026-11-01 | W1 | dev | 2026-11-01-r21-W1-1 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; seed step's SET cell when nothing reads itself |
| 2026-11-01 | W1 | dev | 2026-11-01-r21-W1-2 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; compared both Partitions |
| 2026-11-01 | W2 | dev | 2026-11-01-r21-W2-1 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions |
| 2026-11-01 | W3 | dev | 2026-11-01-r21-W3-3 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; 0 questions; --cells numbering (code cells) not said in the README |
| 2026-11-01 | W2 | dev | 2026-11-01-r21-W2-2 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; --cells counts code cells; Key of ops.job_runs unsaid in README |
| 2026-11-01 | W2 | dev | 2026-11-01-r21-W2-3 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; new_table text could say references Workflow first; Key answered before checking uniqueness |
| 2026-11-01 | W3 | dev | 2026-11-01-r21-W3-1 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; escaping quotes in a hand-edited decisions cell; CONVERSION opt-out reason unsaid |
| 2026-11-01 | H1 | held_out | 2026-11-01-r21-H1-1 | pass | 0 | tickets 21 and 22 rerun, main 2109ed37; --cells counts code cells; compare checks only the latest Partition |
| 2026-11-01 | E1 | dev | 2026-11-01-r21-E1-2 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; ran workbook_text.py, attached the .txt; 1 question |
| 2026-11-01 | E1 | dev | 2026-11-01-r21-E1-1 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; workbook_text.py's .txt attached; Project folder's place unsaid; 1 question |
| 2026-11-01 | E1 | dev | 2026-11-01-r21-E1-3 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; batch named for the target; CONVERSION note repeated three times; 1 question |
| 2026-11-01 | E2 | dev | 2026-11-01-r21-E2-1 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; step CTE with a lookup join; 1 question |
| 2026-11-01 | E2 | dev | 2026-11-01-r21-E2-3 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; typed groups hard-coded, as the workbook typed them; 1 question |
| 2026-11-01 | E3 | dev | 2026-11-01-r21-E3-1 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; query-to-Table-to-formula chain as one CTE; Total Row left out on ask; 1 question |
| 2026-11-01 | E4 | held_out | 2026-11-01-r21-E4-1 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; Parameters value and typed-over value carried; held-out; 1 question |
| 2026-11-01 | E3 | dev | 2026-11-01-r21-E3-3 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; typed dates as groups miss later days, unsaid; Total Row dropped by the user; 1 question |
| 2026-11-01 | E2 | dev | 2026-11-01-r21-E2-2 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; step CTE with a lookup join; 1 question |
| 2026-11-01 | E3 | dev | 2026-11-01-r21-E3-2 | pass | 1 | tickets 21 and 22 rerun, main 2109ed37; query chain as one CTE; Total Row block dropped; 1 question |

## The tickets 21 and 22 round, 2026-11-01: ticket 20's findings fixed, and the workbook as text

Main's tree was built from 2109ed37, which holds tickets 21 and 22:
- `copilot/workbook_text.py` writes a workbook as text, with its M, in dependency order. Step 12
  of the Steps sheet and README step 2 say to attach that text in place of the workbook;
- file 15 reads that order and writes each CTE after every CTE it reads;
- the TODO lines left are named, and change_a_saved_table's step 2 runs its check;
- the runner takes `--list` and `--cells` either side of the path;
- the README's convert naming, RENAME and section endings are reworded.

Each dev scenario ran three times and each held-out one once. Every phase had a fresh Haiku
agent, and both Copilot steps ran on Haiku. The 27 rows are just above.

| scenario | split | passed | questions | the ticket 20 round |
|---|---|---|---|---|
| W1 | dev | 3/3 | 0 | 3/3, 0 |
| W2 | dev | 3/3 | 0 | 3/3, 0 |
| W3 | dev | 3/3 | 0 | 3/3, 0 |
| W4 | dev | 3/3 | 0 | 3/3, 0 |
| W5 | dev | 3/3 | 0 | 3/3, 0 |
| E1 | dev | 3/3 | 1 each, the convert | 3/3, 1 each |
| E2 | dev | 3/3 | 1 each, the convert | 3/3, 1 each |
| E3 | dev | 3/3 | 1 each, the convert | 3/3, 1 each |
| H1 | held out | 1/1 | 0 | 1/1, 0 |
| H2 | held out | 1/1 | 0 | 1/1, 0 |
| E4 | held out | 1/1 | 1, the convert | 1/1, 1 |

What the tickets did:
- **The text.** Every Excel phase 2 ran `workbook_text.py` and attached the .txt with files 15,
  11 and 12, as step 12 says. E2-3 and E3-2 also ran it in phase 1, as a check. No run met a
  loop.
- **The order.** Each chain came back with its steps first:
  - E2 and E4 put job_runs, a step with a lookup column, in a CTE before the summaries that
    read it.
  - E3 put CleanRuns, a query feeding a Table, in a CTE before daily.
  - Every compare passed.
- **The fixes.**
  - W5's step 2 cell ran SHOW PARTITIONS itself.
  - The runner's flags worked either side of the path.
  - The RENAME and naming text was followed (W1-3, H1).
- E4's Parameters value (50) and its typed-over value (job 3, 1000) both came through.

A slip on my side: E3-1's phase 1 was started twice. I stopped the second agent at once. The
run's folder held only the first agent's workbook.

A harness fault, now fixed: two of the ten route proxies (E3-1, E3-2) named file 15 alone. The
route message asked for "the one Copilot file ... and nothing else", against file 00's
three-file rule for a workbook. Those two runs were answered with files 15, 11 and 12, as file
00 says. `route` now asks for the file "with any file file 00 says goes with it".

### Found in the tickets 21 and 22 round, none failing a run

- **The runner's cell numbers (W2-2, W2-3, W3-3, H1).** `--cells` counts code cells only. The
  README and the Workflows' step text don't say so. H1 first ran `--cells 10` for create and
  got do_next.
- **A source's Key (W2-2, W2-3).** The references Workflow asks for the Key before anything
  says how to check one is unique. check_key comes later.
- **Hand-edited cells (W3-1).** With no Jupyter, a decisions cell is edited as JSON. Its quotes
  need `\"`, which nothing shows.
- **The CONVERSION opt-out (W3-1, E1-3).**
  - The note doesn't say what the Toolbox would have refused.
  - project.check()'s "Noted by ..., which blocks nothing" comes before the next step, so it
    reads as a blocker.
  - batch.md and checklist.md repeat one note three times.
- **The convert Workflow.**
  - The seed step's SET cell runs when nothing reads itself (W1-1).
  - check()'s Done-when line is missing after convert (W3-2).
  - Compare checks the latest Partition only, and another needs `partition=` (H1).
- **References (W4-1, W4-2).** The Workflow step doesn't say deleting `does_not_add_up`'s TODO
  means no column. check() names a pending Reference sheet refresh without saying why.
- **The Project folder (E1-1, H1).** Nothing says where the Project folder goes or what to call
  it.
- **Excel.**
  - Step 6 doesn't say whether a text literal in a formula, such as "FAILED", is a fixed value
    for Parameters (E1-3, phase 1).
  - A summary's typed groups become fixed values in the Hive, so a later day or team is left
    out. Nothing tells the user (E3-3, E2-3).
  - A Parameters value is typed into the Hive, so a changed rate won't reach the table
    (E4-1). Neither point is said where the user reads the map.
| 2026-11-01 | W1 | dev | 2026-11-01-r24-W1-1 | pass | 0 | tickets 23 and 24 rerun, main 211907ae; RENAME used; compared both Partitions with partition= |
| 2026-11-01 | W1 | dev | 2026-11-01-r24-W1-2 | pass | 0 | tickets 23 and 24 rerun, main 211907ae; references Workflow first, unsaid in the convert how-to; flagged the original's 14x join |
| 2026-11-01 | W1 | dev | 2026-11-01-r24-W1-3 | pass | 0 | tickets 23 and 24 rerun, main 211907ae; compared the other Partition from a script |
| 2026-11-01 | W3 | dev | 2026-11-01-r24-W3-1 | pass | 0 | tickets 23 and 24 rerun, main 211907ae; ran a wrong --cells once, as its own count; a dev-only job's end unsaid |
| 2026-11-01 | W3 | dev | 2026-11-01-r24-W3-2 | pass | 0 | tickets 23 and 24 rerun, main 211907ae; seed sent nothing, as said |
| 2026-11-01 | W3 | dev | 2026-11-01-r24-W3-3 | pass | 0 | tickets 23 and 24 rerun, main 211907ae; new_table from a query; its Next line's order differs from the notebook's |
| 2026-11-01 | H1 | held_out | 2026-11-01-r24-H1-1 | pass | 0 | tickets 23 and 24 rerun, main 211907ae; convert then promote; promote filled team_prod locations; --cells numbering once |
| 2026-11-01 | E1 | dev | 2026-11-01-r24-E1-3 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; typed groups named in the map; 1 question |
| 2026-11-01 | E1 | dev | 2026-11-01-r24-E1-2 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; typed groups named; 1 question |
| 2026-11-01 | E1 | dev | 2026-11-01-r24-E1-1 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; typed groups named; re-ran convert once, harmless; 1 question |
| 2026-11-01 | E2 | dev | 2026-11-01-r24-E2-2 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; typed teams named in the map; 1 question |
| 2026-11-01 | E2 | dev | 2026-11-01-r24-E2-1 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; TODO lines left, as they wait on nothing; 1 question |
| 2026-11-01 | E2 | dev | 2026-11-01-r24-E2-3 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; Done heading for the batch seen; TODO lines left; 1 question |
| 2026-11-01 | E3 | dev | 2026-11-01-r24-E3-1 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; query chain as one CTE; typed days named; Total Row left out on ask; 1 question |
| 2026-11-01 | E3 | dev | 2026-11-01-r24-E3-3 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; ran a write before its decisions, refused clearly; typed days named; 1 question |
| 2026-11-01 | E4 | held_out | 2026-11-01-r24-E4-1 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; Parameters value written in, named; typed-over value carried; held-out; 1 question |
| 2026-11-01 | E3 | dev | 2026-11-01-r24-E3-2 | pass | 1 | tickets 23 and 24 rerun, main 211907ae; Total Row block dropped; typed days named; 1 question |

## The tickets 23 and 24 round, 2026-11-01: targeted, the paths those tickets changed

Main's tree was built from 211907ae, which holds tickets 23 and 24:
- the CONVERSION notes say what the Toolbox refuses, and say it once;
- check() names a finished batch and says why a Reference sheet needs a refresh;
- the seed cells say when they seed nothing, and the references Key step explains check_key;
- the README says where a Project folder goes;
- step 6 keeps a value a formula matches on, and file 11 has Copilot name in the map any value written into the Hive;
- promote has a Copilot file of its own, 16.

The user OKd a targeted round (2026-11-01). It ran the scenarios whose paths the two tickets
changed: convert (W1, W3), convert then promote (H1), and the Excel path (E1 to E4). W2, W4, W5
and H2 were left out, as nothing they run changed since the tickets 21 and 22 round, where each
passed. Every phase had a fresh Haiku agent, and both Copilot steps ran on Haiku. The 17 rows
are just above.

| scenario | split | passed | questions | the tickets 21 and 22 round |
|---|---|---|---|---|
| W1 | dev | 3/3 | 0 | 3/3, 0 |
| W3 | dev | 3/3 | 0 | 3/3, 0 |
| H1 | held out | 1/1 | 0 | 1/1, 0 |
| E1 | dev | 3/3 | 1 each, the convert | 3/3, 1 each |
| E2 | dev | 3/3 | 1 each, the convert | 3/3, 1 each |
| E3 | dev | 3/3 | 1 each, the convert | 3/3, 1 each |
| E4 | held out | 1/1 | 1, the convert | 1/1, 1 |

What the tickets did:
- **The map notes.** Every Excel answer named its summary's typed-in groups, saying a later day
  or team won't be in the table. Each run said so back to its manager. E4 named its Parameters
  value written into the Hive.
- **Routing.** Every route proxy named files 15, 11 and 12. The route message now asks for any
  file file 00 says goes with one, and no run lost a file.
- **check() and the seed cells.**
  - check() named each finished batch done (W3-1, W3-3, E2-3).
  - The seed cells printed that they seeded nothing (W1-1, W3-2, H1).
  - H1 promoted with file 16's Workflow, and promote filled each prod location.
- **step 6.** No run moved "FAILED" into Parameters.

### Found in the tickets 23 and 24 round, none failing a run

- **The runner's cell numbers (W3-1, H1).** Two runs counted the notebook's own cells and ran the
  wrong one once. `--list` gave the right number. The message says so; the notebook doesn't.
- **new_table's convert step (W3-3).** Its "Next:" line says to answer the Decisions, then run the
  next steps. The notebook's order is preview, then reference_from_logic, then the Decisions.
- **Comparing another Partition (W1-3, H1).** Once the batch is in `finished/`, another Partition
  is compared from a script, with compare_batch's `partition=`. The step says how, but no cell
  holds it.
- **Excel, step 5 (E2-1).** It doesn't say what to name a summary Table. Each run named it for its
  sheet or file.
- **X69 (Excel held out, two rounds running).** Copilot gives a passed-through dt the date held as
  text conversion. File 11's rule says "a date held as text", with no word on a column no formula
  reads.
- **The harness: proxy reads.** An Excel proxy message of five workbooks ran past what a proxy
  reads at once (about 600 lines), so it answered only the first four. Each missing task was run
  again on its own, and each passed. Groups of two hold.
| 2026-11-05 | W7 | dev | 2026-11-05-W7-3 | pass | 0 | passed; Run value's file imports taken from latest_partition's docstring |
| 2026-11-05 | W7 | dev | 2026-11-05-W7-1 | pass | 0 | passed; Run value file and register written by hand from docstrings |
| 2026-11-05 | W7 | dev | 2026-11-05-W7-2 | pass | 0 | passed; Run value file and register written by hand from docstrings |

## The ticket 14 round, 2026-11-05: W7, a Run value and a seed limit

Main's tree was built from dev at 8.4 (ac53eac1). Three fresh Haiku runs of the new scenario W7:
convert the team's run_log.hql, its PERIOD_END tag answered by a Run value worked out at each
write, its seed copying only 2026-09-24 on. The three rows are just above.

| scenario | split | passed | questions | cells added |
|---|---|---|---|---|
| W7 | dev | 3/3 | 0 | 0 |

What it showed:
- **Run values.** Each run wrote `period_end()` returning `latest_partition(job_runs.dt, query)`
  in building_blocks/run_values.py, registered it, and answered PERIOD_END with the function.
  Each write's Hive held the day worked out then, 2026-09-24.
- **Seed limits.** Each answered `"seed": {"dt": {"from": "2026-09-24"}}`; the seed copied 4
  rows, and the compare passed on 2026-09-24 (and on 2026-09-23, which two runs checked too).
- **No cell of your own.** No run's Workflow notebook held a code cell more than the Toolbox
  wrote: the `project.check()` cell under each decision step was the one used.

### Found in the ticket 14 round, none failing a run

- **The Run value's file (all three).** Its imports and `project.register("run_values")` were
  taken from `latest_partition`'s docstring and how-to 09; no README step shows the file. Each
  run registered from a script, outside the notebooks.
- **The Run value's Table reference (W7-2, W7-3).** `from references.ops__job_runs import
  job_runs` needs that reference first, its TODO lines filled; two runs found it on the import's
  error.
- **RENAME (W7-2, W7-3).** The default name is mart_dev.run_log_mart; the names cell's RENAME
  rule is what drops the suffix, and two runs found it late.
- **The seed's edge (W7-1, W7-2).** The first write's window, PERIOD_END-1 to PERIOD_END, adds
  2026-09-23's rows the seed left out. Each run said so, matching the original. Expected, and
  how-to 09 could say it.
| 2026-11-06 | W1 | dev | 2026-11-06-W1-1 | pass | 0 | 8.5 round; 5 actions |
| 2026-11-06 | W1 | dev | 2026-11-06-W1-2 | pass | 0 | 8.5 round; 4 actions |
| 2026-11-06 | W1 | dev | 2026-11-06-W1-3 | pass | 0 | 8.5 round; 4 actions |
| 2026-11-06 | W3 | dev | 2026-11-06-W3-1 | pass | 0 | 8.5 round; 6 actions |
| 2026-11-06 | W3 | dev | 2026-11-06-W3-2 | pass | 0 | 8.5 round; 7 actions |
| 2026-11-06 | W3 | dev | 2026-11-06-W3-3 | pass | 0 | 8.5 round; 10 actions |
| 2026-11-06 | W7 | dev | 2026-11-06-W7-1 | pass | 0 | 8.5 round; 5 actions |
| 2026-11-06 | W7 | dev | 2026-11-06-W7-2 | pass | 0 | 8.5 round; 17 actions |
| 2026-11-06 | W7 | dev | 2026-11-06-W7-3 | pass | 0 | 8.5 round; 6 actions |
| 2026-11-06 | H1 | held_out | 2026-11-06-H1-1 | pass | 0 | 8.5 round; 8 actions |
| 2026-11-06 | H1 | held_out | 2026-11-06-H1-2 | pass | 0 | 8.5 round; 5 actions |
| 2026-11-06 | H1 | held_out | 2026-11-06-H1-3 | pass | 0 | 8.5 round; 9 actions |

## The 8.5 round, 2026-11-06: fewer of the user's actions

Main's tree was built from dev at 8.5 (2dbb8a12). A round of the scenarios 8.5 changed the
path of: convert (W1, W3), a Run value and a seed limit (W7) and convert then promote (H1),
three fresh Haiku runs each, one phase each. The 12 rows are just above; each row's note
counts its actions (Toolbox 8.5's ticket 12: cells edited in a Workflow notebook from as the
Toolbox writes them, and files of the run's own).

| scenario | split | passed | questions | files of its own, 8.4 | files of its own, 8.5 |
|---|---|---|---|---|---|
| W1 | dev | 3/3 | 0 | 5, 6, 5 | 4, 3, 3 |
| W3 | dev | 3/3 | 0 | 6, 7, 12 | 4, 4, 7 |
| W7 | dev | 3/3 | 0 | 5, 5, 10 | 3, 13, 4 |
| H1 | held out | 3/3 | 0 | 5 (one run) | 6, 3, 7 |

"Files of its own" counts what a run wrote outside its Project, its helper scripts among
them (the loop's agents have no Jupyter, so most write a script to set a cell), and each
script saved into the Project for a Workflow. 8.4's are counted the same way from its kept
runs (the tickets 23 and 24 round, and ticket 14's W7). Cells edited are counted only for 8.5,
as 8.4's notebooks were written by 8.4.

What 8.5 did:
- **The names cell.** Every W1, W7 and H1 run, and two of three W3 runs, gave FILES a path
  where the script is: no copy saved beside the notebook. Promote's TABLES left [] promoted
  every finished table (H1-1, H1-2).
- **Locations placed.** No run answered a location: each table was placed under DEV's root,
  each prod copy under PROD's.
- **Run values.** All three W7 runs wrote `project.new_run_value(...)` at the top of the
  decisions cell; none wrote run_values.py by hand or called register.
- **Read straight down.** No run scrolled back: the run cells, then the decisions cell, then
  "Run the rest". Several had nothing to answer at all.

### Found in the 8.5 round, none failing a run

- **"Run up to your Decisions" ran to the end with nothing open** (W1, W3, H1, every run).
  Correct, but read as a surprise: each expected a stop. Mended after the round: its cell's
  text and the README's step 2 say it runs to the end, writing and comparing, when nothing
  waits on you, with dry_run=True to see first.
- **Promote's report said "fill in location=" when each was placed** (H1-2, H1-3). Mended
  after the round: it names a table only when its Table reference has none.
- **Accepting a proposed Key once the batch had finished** (W3-1, W3-3): "Run the rest" skips
  a finished batch, so `"key": "proposed"` was written only by calling write_decisions. A Key
  convert proposes is kept anyway; accepting it only takes off the mark. For a later round.
- **A finished batch compared again** (W7-1, H1-1): one run found "Run the rest" compared the
  listed Partition and step 7's own cell didn't; another the other way round. To check.
- **A convert's TODO lines** (W3-1, W3-3): its Table reference's first line and
  does_not_add_up, which check() doesn't list; and new_run_value's printed import line went
  unseen when run through the runner (W7-1).
- **statement.hql of a table from a multi-INSERT FROM** shows the whole statement (H1-2,
  H1-3), where in_dev.hql has the table's own.
- **The harness**: the runner's cell numbers are code cells only (W3-3, W7-3); a FILES path
  that doesn't exist printed nothing through the runner (W7-3).
| 2026-11-09 | W1 | dev | 2026-11-09-W1-2 | pass | 0 | passed with no question; RENAME needed to keep the name; a Windows path's backslashes failed in sys.path.append; another run's file in the shared scratchpad; 8 actions; inputs 5dd96ac865f72551 |
| 2026-11-09 | W1 | dev | 2026-11-09-W1-1 | pass | 0 | passed with no question; the 117 KB README searched by heading; --cells numbers code cells, unsaid; a TODO line's blocking unsaid; 4 actions; inputs 5dd96ac865f72551 |
| 2026-11-09 | W1 | dev | 2026-11-09-W1-3 | pass | 0 | passed with no question; a run without a notebook unsaid in section 1; FILES outside the Project unclear in step 1; 4 actions; inputs 5dd96ac865f72551 |
| 2026-11-09 | W8 | dev | 2026-11-09-W8-3 | pass | 0 | passed with no question; writing a table for a chosen period (write_days in statements()) unsaid in the README; a plain parameter default unsaid; hand-editing a notebook's JSON; 6 actions; inputs db651039d61563a0 |
| 2026-11-09 | W8 | dev | 2026-11-09-W8-1 | pass | 0 | passed with no question; write_days for a chosen period unsaid in the README; a write in statements() taking the added one's place unsaid; run_value against reading WEEK unsaid; 6 actions; inputs db651039d61563a0 |
| 2026-11-09 | W8 | dev | 2026-11-09-W8-2 | pass | 0 | passed with no question; WEEK bare with no default, so a Jupyter run needs it set; notebooks edited by script; scratch files in the shared scratchpad; 6 actions; inputs db651039d61563a0 |

## The 8.6 round, 2026-11-09: connect, and a Scheduled run

Main's tree was built from dev at 8.6 (e2776efc). A round of the scenarios 8.6 changed the
path of: convert (W1), whose notebooks now connect at their top, and the new W8, a Scheduled
run of a week's breakdown given its week as text; three fresh Haiku runs each, one phase each.
The 6 rows are just above. It is the first round the loop records its inputs for (ticket 11):
each row ends with its inputs hash, and `plan W1 W8` now answers memoized for both, so the
next round gives neither to an agent until something a run reads changes.

| scenario | split | passed | questions | actions | files of its own, 8.5 | files of its own, 8.6 |
|---|---|---|---|---|---|---|
| W1 | dev | 3/3 | 0 | 4, 8, 4 | 4, 3, 3 | 3, 7, 3 |
| W8 | dev | 3/3 | 0 | 6, 6, 6 | new | 6, 6, 6 |

What 8.6 did:
- **connect.** Every W1 run filled the convert notebook's `connect(...)` line with the team's
  connection, as the README says, and asked nothing.
- **Scheduled runs.** Every W8 run made its run through `admin/scheduled_runs.ipynb`'s
  `NEW_RUNS`, typed its parameter with a hint, built it to read the Hive, and ran it top to
  bottom with the week passed as text; each table holds exactly the week asked for.

### Found in the 8.6 round, none failing a run

- **A run of a chosen period** (W8, all three): writing a table for the week asked for takes
  each Table notebook's `write_days(first_day, last_day)` in `statements()`, which the README's
  Scheduled runs section and the Template never name; each run found it in the logic's
  docstrings. Nor does the README say that a write in `statements()` takes the place of the
  one the build would add for that table (W8-1), which the code does.
- **Parameter defaults** (W8-2, W8-3): the README's examples are all `| None`; one run left
  WEEK with no default, one gave a plain date, with no word on either.
- **run_value or the parameter itself** (W8-1): the Template shows `run_value(...)` for a value
  worked out each build; reading the parameter inside `statements()` works too, and nothing
  says which to pick.
- **W1, as in 8.5**: `--cells` numbers code cells only, unsaid (W1-1); the README is long
  enough that the convert steps are found by heading (W1-1); whether a Table reference's TODO
  line blocks a run is unsaid (W1-1); a Windows path's backslashes failed in
  `sys.path.append` (W1-2); FILES pointing outside the Project read as unclear in step 1 (W1-3).
- **The harness**: the runs' agents share the session's scratchpad folder, so one run's
  script was overwritten by another's (W1-2) and others left scratch files there (W8-2): give
  each run a scratch folder of its own, or tell the agent to keep scripts in `my_work/`.
