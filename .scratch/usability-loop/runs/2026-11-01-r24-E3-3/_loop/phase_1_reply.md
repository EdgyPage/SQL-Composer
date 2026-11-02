DONE: Made `my_work/daily_runs_formula.xlsx` from the blank Formula workbook and filled it in as its Steps sheet says. The data team converts it from here (step 12 hands the rest to them), so I did not run Copilot or `workbook_text.py`.

What is in the workbook:
- **job_runs** (sheet and Table): the nine raw rows from `from_your_team/daily_runs.xlsx`'s Raw sheet, as values. Row 1 says "Copied from ops.job_runs" (step 2), the header is row 2, and the Table is A2:F11. Run 98 (no status) and run 99 (TEST) are kept, since the query removes them.
- **Power Query** sheet: the team's CleanRuns M, with its source changed to `Excel.CurrentWorkbook(){[Name="job_runs"]}`. Its header note says it is typed in, not loaded.
- **CleanRuns** (sheet and Table): the seven rows the query gives (runs 95, 96, 97, 101, 102, 103, 104), typed in. I could not add the query in Excel here, so I used the fallback in step 7. The Steps sheet and example 03 both describe it.
- **daily** (sheet and Table, A1:C4): columns `dt`, `runs` and `total_duration_mins`. The two day rows use `COUNTIFS` and `SUMIFS` on `CleanRuns`, written as `daily[[#This Row],[dt]]`. The Total Row sums both figures with `SUBTOTAL(109, ...)`. The old note in E1 is kept.
- **Steps**, **Parameters** and **Keys** are unchanged and empty. No formula uses a fixed value, and no value was typed over a formula, so neither needs a row.

Once Excel opens it, the formulas should give 3 runs and 60 minutes for 2026-09-23, 4 runs and 100 minutes for 2026-09-24, and a total of 7 runs and 160 minutes. openpyxl saves no calculated values, so Excel computes them on open.

Side effect: to build the file I briefly wrote a scratch folder, `C:/Users/myfir/AppData/Local/Temp/usability-loop/scratch_e3_3`, outside the work folder. I deleted it. The other `scratch_inspect_E2_3.py` in that parent folder is not mine.

Path of the deliverable: `C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E3-3/my_work/daily_runs_formula.xlsx`
