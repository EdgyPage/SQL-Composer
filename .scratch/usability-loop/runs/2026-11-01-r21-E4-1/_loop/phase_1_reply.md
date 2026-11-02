DONE: Made my_work/costs_formula.xlsx from a copy of main/copilot/formula_workbook.xlsx, filled in per its Steps sheet, and saved it. The template itself is unchanged. No Copilot questions were needed.

Saved file: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E4-1\my_work\costs_formula.xlsx

What is in it (sheets: Steps, Parameters, Keys, jobs, job_runs, job_costs, team_runs):
- Parameters (step 6): cents_a_minute = 50, from the Rate sheet. Used by the job_costs formulas through XLOOKUP.
- Keys (step 10): job_costs with job_id, because job 3's cost was typed over a formula.
- jobs (steps 1 to 3): raw data, a Table named jobs. Row 1 says "Copied from ops.jobs in our warehouse." The header is row 2.
- job_runs (steps 1 to 3): raw data, a Table named job_runs. Row 1 says "Copied from ops.job_runs in our warehouse." The header is row 2. It has a formula column team (step 5): XLOOKUP of job_id in jobs. This lets team_runs count runs by team.
- job_costs (step 5): a summary Table with one row per job_id. cost_cents = SUMIFS of job_runs duration_mins by job_id, times cents_a_minute. Job 3's row is the typed value 1000, kept as the source note says ("as agreed").
- team_runs (step 5): a summary Table with one row per team (data, finance, web). runs = COUNTIFS of job_runs team. The counts match the source's SUMPRODUCT: data 4, finance 5, web 0.
- Power Query, running totals, Total Rows: none needed. The source has none of them.
- The Steps sheet, Parameters and Keys were kept, as the three example workbooks keep them. No Hive sheet was added.

Things to know:
- Job 3's typed-over value (1000) does not match its formula. The formula would give 60 minutes times 50, which is 3000. I kept 1000 because the source note says it was typed in by hand, as agreed. The data team should confirm it.
- Step 12 says the data team converts the workbook, so I did not run workbook_text.py or any Copilot step. I did not send the file anywhere.
- The formulas use the long structured-reference form and _xlfn.XLOOKUP, as the example workbooks do. Excel has not opened the file, so it was not checked there.
- Scripts were run from the shell's standard input, so nothing else was written into my_work. _loop/ and the other top-level files in the work folder were not touched.
