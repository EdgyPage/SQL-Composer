DONE: Made the Formula workbook copy and filled it in as its Steps sheet says. Saved at C:\Users\myfir\Code and Repos\... no: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E2-2\my_work\team_report_formula.xlsx

What is in it (checked by reading the saved file back, and against the source numbers):
- jobs (sheet jobs, A2:D6): the Jobs sheet's job_id, job_name, team, region as values. Row 1 holds "Copied from ops.jobs in our warehouse." (step 2 says to put the source note above the header, so the old F1 note moved there.) Header is row 2.
- job_runs (sheet job_runs, A2:G11): the Runs sheet's run_id, job_id, status, duration_mins, avg_retry_secs, dt as values, with row 1 "Copied from ops.job_runs in our warehouse; team looked up from Jobs." The team column (G) is rebuilt as a formula per row, _xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]), in place of the old VLOOKUP on Jobs!A:C (step 5, reading another Table by name). Its calculated-column formula is set too, so new rows fill down.
- teams (sheet teams, A2:C5): the Teams summary as a Table of its own, with the team names typed in row 1-note-below (note in A1). runs = COUNTIFS(job_runs[team], teams[[#This Row],[team]]); total_duration_mins = SUMIFS(job_runs[duration_mins], job_runs[team], teams[[#This Row],[team]]). This replaces the whole-column COUNTIF/SUMIF on Runs!G:G and D:D.
- Parameters and Keys left empty: no formula uses a fixed value, and no formula cell had a value typed over it (steps 6 and 10). Steps sheet kept as it was. No Total Row was needed: the Teams sheet had none.
- Table names: jobs and job_runs take the part after the dot of ops.jobs and ops.job_runs (step 2); teams has no database source, so it gets a name with no spaces.

Expected figures the data team should see after conversion (from the source data, matching the original Teams sheet's formulas): data 4 runs, 67 minutes; finance 5 runs, 113 minutes; web 0 runs, 0 minutes (cache_warm has no runs).

Things to know:
- Run 98 has no status in the source; it is left blank, not filled in.
- dt is kept as text, as in the source.
- Not opened in Excel (not available here). Formulas are written in the file form the examples use (_xlfn.XLOOKUP), and openpyxl stores no calculated values, so Excel works them out on opening.
- Step 12 (Copilot conversion, or sending the file on) is the data team's, as the Steps sheet says; I did not run workbook_text.py or ask Copilot. The file is ready to send.
- Nothing was written outside my_work/, and _loop/ was not touched.
