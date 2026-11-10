# Beginner reader: the cleanup before the round (2026-11-09)

The `beginner-reader` agent (model `opus`), over only the texts the cleanup changed (uncommitted
then): WAREHOUSE_TEXT; the README's `warehouse.py` bullet and its Scheduled runs section's
opening, `leave_out=`, run-again and `RUNS` sentences; how-to 31's running again; the
project_templates module docstring and the scheduled_run Template's step 5, `# scheduled`,
Build and Run comments; weekly_team's source; the untagged-parameters refusal; the docstrings
of build_run, export_project_lineage and remove_scheduled_run; the Table notebooks' "The code
cells" line; Copilot file 18's `run_values=` bullet. Its report, as given, but shortened (line
numbers are of the files before the mends). What was done with each stop is in ticket 10's
Answer, under "Cleanup before the round".

## A test it found failing

`tests/test_docstrings.py::test_the_worked_example_runs[project.export_project_lineage]`: the
Template's `# scheduled` comment grew a line, so the `<...>` moved from line 12 of cell 4 to
line 13, and the docstring still said line 12.

## Stops

1. **WAREHOUSE_TEXT, lines 221-224**: "In a notebook ... in a Scheduled run" reads as if a
   Scheduled run weren't a notebook; "which one" means query or execute. A moment.
2. **WAREHOUSE_TEXT, line 225**: "change connect, query and execute below to call yours":
   connect calls nothing, it checks two names; its refusal says it better. A moment.
3. **WAREHOUSE_TEXT, line 228**: 109 characters, a broken wrap. A moment.
4. **README lines 159-162**: points at connect's refusal, never seen until a failure; "three
   functions", when the file has more. A reread.
5. **README lines 1398-1403**: "only because" in `leave_out=` parsed twice; the
   `run_values=` line below it a reread too. A reread.
6. **README lines 1417-1420**: `INSERT_INTO` appears nowhere else in the README; nothing says
   how to tell whether a run holds one (the Build cell's `INSERT INTO TABLE` against
   `INSERT OVERWRITE TABLE`); "replaces the Partitions it fills" leaves out a table with none.
   A reread.
7. **README lines 1455-1457, the `RUNS` bullet**: "a name the `# scheduled` cell uses is
   defined in that cell or the parameters cell" is contradicted by the setup cell's imports;
   "never their connect(...)" leaves no way for weekly_team's `latest_partition(..., query)`
   to export, the answer (admin/scheduled_runs.ipynb's first cell connects) only in
   export_run_hive's docstring. Stuck.
8. **How-to 31, lines 370-373**: the Run output doesn't show the first two writes are
   overwrites; and does a run again with `START_FROM mart.team_days` give back
   `results["team_day"]`, a SELECT sent first? A reread.
9. **project_templates line 12, and the Table notebooks' "The code cells" line**: "your
   query" reads as a SQL query, and the cell's heading, "# 1. The Project and your query",
   doesn't match "1 the Project, your connection and your query". A moment.
10. **Template lines 551-553**: "a function ... each time it is built, passed as
    run_value(function)": a function isn't built; passed where? A reread.
11. **Template lines 564-567, the Build comment**: `period_end` appears nowhere in the
    notebook; "leaves out a table it would write" says less than the README. A moment.
12. **weekly_team lines 50-52**: "the two tables mart.team_days reads" unnamed. A moment.
13. **weekly_team line 58**: 102 characters. A moment.
14. **weekly_team's generated text cell** (not changed): still lists the `<...>` to fill in,
    though none are left. A moment.
15. **The untagged-parameters refusal**: clear; VS Code's command name unchecked. A moment.
16. **build_run, lines 7350-7352**: a `#` inside a `#` comment. A moment.
17. **build_run, line 7351**: why set `START_FROM` by hand if the build reads the file? A
    reread.
18. **build_run, lines 7385-7388**: "It reaches every Statement built" ("it"?), and a
    128-character line. A reread.
19. **export_project_lineage, lines 7462-7471**: clear, but "at its line 12" is wrong (above).
    A reread, verging on stuck.
20. **Copilot file 18, lines 59-62**: three nested phrases before the point, and "you ...
    yourself" where the file says "the user". A reread, close to stuck.

No stop: the README's opening sentence, the Template's step 5 and Run cell,
`remove_scheduled_run`'s example and sentence.

## The three costliest

1. The README's `RUNS` bullet (7).
2. export_project_lineage's "at its line 12" (19), and its failing test.
3. The `run_values=` wording, four ways in four places, worst in Copilot file 18 (18, 20, 11,
   5).
