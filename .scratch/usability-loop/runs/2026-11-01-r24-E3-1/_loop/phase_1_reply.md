DONE: Made my_work/daily_runs_formula.xlsx, a copy of the empty main/copilot/formula_workbook.xlsx, filled in as its Steps sheet says. Full path: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E3-1\my_work\daily_runs_formula.xlsx

What is in it:
- Steps, Parameters and Keys sheets kept as the template has them. Parameters and Keys stay empty (step 6: no formula uses a fixed value, and "TEST" stays in the query as a value a rule matches on; step 10: no value was typed over a formula).
- Raw (steps 1 to 2): the team's Raw data pasted as values, with the row above the header reading "Copied from ops.job_runs in our warehouse." (the team's own note). The data is a Table named job_runs over A2:F11. The name comes from the part after the dot in ops.job_runs, as step 2 says.
- Power Query (step 7, fallback): cell A1 reads "Query CleanRuns:", and cell A2 holds the team's M. Its source line now reads Excel.CurrentWorkbook(){[Name="job_runs"]}[Content] rather than "Raw", since the Table was renamed. I used the fallback because openpyxl cannot add a real Power Query, and Excel isn't available here. So this is not a live query: it is the M text only.
- Clean (step 7, fallback): the 7 rows the M keeps (runs 95, 96, 97, 101, 102, 103, 104), typed into a Table named CleanRuns over A1:F8. I checked them against the M's rule (no null status, status not TEST), and they match.
- Daily (step 5): a summary Table named daily over A1:C4, with columns dt, runs (COUNTIFS on CleanRuns) and total_duration_mins (SUMIFS on CleanRuns). The Total Row is on, with SUM for runs and total_duration_mins. Formulas use the file form of the structured references, e.g. daily[[#This Row],[dt]].

Things I did not do:
- I did not send the file to the data team, and I did not run Copilot, since step 12 says the data team converts it. I did not run workbook_text.py.
- Excel has not calculated the formulas. The workbook is set to recalculate on open. Expected results from the data: 2026-09-23 has 3 runs and 60 minutes; 2026-09-24 has 4 runs and 100 minutes; the total row shows 7 runs and 160 minutes.

Checks I made: reloaded the saved file and confirmed the sheets, the three Tables and the Total Row settings. I did not touch main/, from_your_team/ or _loop/. My helper scripts are in the scratchpad at C:\Users\myfir\AppData\Local\Temp\claude\C--Users-myfir-Code-and-Repos-SQL-Composer\adb999d6-d2cc-49aa-89d3-e71d06e18fba\scratchpad\build_daily_runs_formula.py (outside the work folder, as the scratchpad rule asks).
