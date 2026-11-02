DONE: Made my_work/daily_runs_formula.xlsx from main/copilot/formula_workbook.xlsx and filled it in as its Steps sheet says. Full path: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-3\my_work\daily_runs_formula.xlsx

What is in it:
- Steps, Parameters, Keys: the template as it was. Steps is unchanged. Parameters and Keys are empty, since no formula uses a fixed value and no value was typed over a formula.
- job_runs (steps 1 to 3): the team's Raw data, values only, columns A to F, 9 records, one header row. I inserted a row above the header with "Copied from ops.job_runs", as step 2 says, and named the Table job_runs. The team's note in H1 was not carried over, since the new row says the same.
- CleanRuns (step 7, fallback): the Power Query's output typed into a Table named CleanRuns, 7 rows. I checked these against the team's Clean sheet and they match.
- Power Query (step 7, fallback): cell A1 reads "Query CleanRuns:" and cell A2 holds the team's M, with the source changed to Excel.CurrentWorkbook(){[Name="job_runs"]}.
- daily (steps 4 and 5): the Daily sheet rebuilt as a summary Table named daily, with dt, runs and total_duration_mins, one row per day. Formulas are COUNTIFS and SUMIFS on CleanRuns, written by column name. Its Total Row is on, with Sum for runs and total_duration_mins. Expected values: 2026-09-23 has 3 runs and 60 minutes, 2026-09-24 has 4 runs and 100 minutes, and the total row shows 7 and 160.

Judgment calls:
- Excel can't open here and openpyxl can't add a Power Query, so I used the fallback in step 7. The query's rows are typed in, not refreshed from Raw.
- The Power Query's filter has the fixed text "TEST". Step 6 covers formulas, so I left it in the M and did not add a Parameters row.
- Step 12 says that when a data team converts the workbook, the rest of the step is theirs. I did not run workbook_text.py or ask Copilot.
- The formulas are not evaluated in Excel. I checked the Table XML and the values by hand.
- My build script is at C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E3-3\my_work\build_daily_runs.py. I left it in my_work.
