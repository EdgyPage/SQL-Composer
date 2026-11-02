DONE: Made my_work/daily_runs_formula.xlsx from a copy of main/copilot/formula_workbook.xlsx, filled in as its Steps sheet says, ready to send to the data team (step 12 says the rest is theirs when someone else converts it).

Full path: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-1\my_work\daily_runs_formula.xlsx

What is in it, by step:
- Steps 1-2: sheet job_runs holds the Raw sheet's six columns as values, with the note "Copied from ops.job_runs in our warehouse." in a row above the header (step 2's Insert-a-row rule). Its Table is named job_runs (A2:F11), the part of ops.job_runs after the dot.
- Steps 3-7: the Clean sheet is the output of your team's Power Query "CleanRuns", which Excel couldn't add here. Following the Power Query fallback in step 7, the sheet Power Query holds "Query CleanRuns:" with its M in the cell below, with the Source line changed to read job_runs. Sheet CleanRuns holds the 7 rows the query gives as a Table named CleanRuns. I checked in Python that those rows match the query's rule (status present and not TEST). Your Clean sheet's Table was named CleanRuns, so I kept that name.
- Step 5: the Daily sheet is now a summary Table named daily_runs (sheet daily_runs, A1:C4) with columns dt, runs and total_duration_mins. Each figure reads CleanRuns by name, e.g. =COUNTIFS(CleanRuns[dt],daily_runs[[#This Row],[dt]]), and the Total Row is on (Table Design > Total Row, Sum for runs and total_duration_mins, label Total).
- Step 6: no fixed values in your formulas, so Parameters stays empty. Step 8: no running totals, so nothing to change. Step 10: no value was typed over a formula, so Keys stays empty.
- Steps 9 and 11: nothing outside the Tables that should be converted, and nothing left outside a Table.

Expected results once Excel calculates: 2026-09-23 has 3 runs and 60 total minutes; 2026-09-24 has 4 runs and 100 minutes; the Total Row shows 7 runs and 160 minutes.

Notes:
- The Steps sheet is kept as the template has it, and so are the Parameters and Keys sheets.
- I didn't run Copilot or workbook_text.py, because step 12 leaves conversion to the data team.
- Nothing outside my_work/ was written; the scripts ran from stdin, so no script file was left behind.
- The Excel-only check (opening the file in Excel to see its calculated values) was not possible here, since Excel can't open here. The formulas are as the examples write them.
