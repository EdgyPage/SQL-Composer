DONE: Made my_work/costs_formula.xlsx from a copy of main/copilot/formula_workbook.xlsx and filled it in by its Steps sheet. Full path: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E4-1\my_work\costs_formula.xlsx. It is ready for the data team to convert. Sending it is their step (Steps step 12), and I did not send it.

What is in the workbook (sheets: Steps, Parameters, Keys, jobs, job_runs, job_costs, team_runs):
- jobs: a Table named jobs (A2:D6), copied as values from the Jobs sheet, with the note "Copied from ops.jobs in our warehouse." in row 1 above the header.
- job_runs: a Table named job_runs (A2:G11), the Runs sheet as values, with the note in row 1. Its column G, team, is a formula: =XLOOKUP(job_id, jobs[job_id], jobs[team]). I added it so Team runs can count runs by team. The raw avg_retry_secs and dt columns are kept as they were.
- job_costs: a Table named job_costs (A1:B5). job_id is typed (1 to 4). cost_cents is a formula, SUMIFS of job_runs[duration_mins] by job_id, times XLOOKUP("cents_a_minute", Parameters). The note from the team's sheet is kept in D1. Job 3's cost is the typed-over value 1000, kept as typed, as the team agreed.
- team_runs: a Table named team_runs (A1:B4). team is typed (data, finance, web). runs is =COUNTIFS(job_runs[team], team_runs[team]). The note is kept in D1.
- Parameters: cents_a_minute = 50 (the team's Rate sheet, which is not carried over).
- Keys: job_costs with key column job_id (for the typed-over cost).

Expected values, worked out by hand because openpyxl writes no cached results and Excel can't open here:
- job_costs: job 1 = 3350, job 2 = 2650, job 3 = 1000 (typed), job 4 = 0.
- team_runs: data = 4, finance = 5, web = 0. These match the team's original SUMPRODUCT logic.

Things for the data team or manager to check:
- The cost formula, like the team's original SUMIF, counts every run of a job, including TEST and FAILED runs. I did not change that.
- Job 3's typed 1000 differs from what the formula would give, which is 3000 (60 minutes at 50). It is kept as typed because the team agreed it.
- Build and check scripts are in my_work/: build_costs_formula.py and dump_workbook.py. Nothing outside my_work was changed, and _loop/ was not touched.

Steps 7 and 8 did not apply (no Power Query, no running totals). I asked Copilot nothing.
