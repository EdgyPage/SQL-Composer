DONE: mart_dev.job_costs and mart_dev.team_runs are built, written and compared in dev, with the Toolbox's convert Workflow, from the Hive Copilot wrote for costs_formula.xlsx.

What I did, in order:
- Read the README, the Workflows section and the convert notebook. Read the workbook's Steps sheet, which says to run workbook_text.py and send the text with Copilot files 15, 11 and 12.
- Ran main/copilot/workbook_text.py on my_work/costs_formula.xlsx. It wrote my_work/costs_formula.txt.
- Made the Project at C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E4-1\my_work\mart_project (a copy of the Toolbox folder, then project.start()).
- Set warehouse.py to `sys.path.append(...)` the work folder and `from team_connection import conn`. A test query worked.
- Set admin/databases.py to DEV = "mart_dev" and PROD = "team_prod". Both databases were empty before I started, so there was no table of someone else's to leave alone.
- Asked Copilot. Its reply, copilot_reply_1.md, gives the Hive for job_costs (summary on job_id, with job 3 typed over as 1000) and team_runs (summary on team, with the typed groups data, finance, web). I saved both as admin/workflows/convert/job_costs.hql and team_runs.hql, with the placeholder <database> filled in as ops, which the workbook's sources name.
- Filled in the convert names cell: NAME = "costs", FILES = ["job_costs.hql", "team_runs.hql"]. Ran convert: two Saved tables in mart_dev. The Table references are references/mart_dev__job_costs.py and references/mart_dev__team_runs.py. Convert also added references for ops.job_runs and ops.jobs from DESCRIBE.
- Answered the two open Decisions in the decisions cell: location "/data/team/mart_dev.db/job_costs" and "/data/team/mart_dev.db/team_runs". The proposed keys (job_id, team) are one row per value, so I kept them.
- Ran the Workflow's steps in order: create (cell 6), write (cell 8), compare (cell 9). Seed (cell 7) I skipped, since neither table reads itself and the notebook says the step is then done once create is. Both compares passed, and the batch moved to admin/workflows/convert/finished/costs/.
- Filled the two Table references' TODO lines: a one-line description of one row, and I deleted the does_not_add_up line, since no column is an average, ratio or distinct count.

Checked results in the warehouse:
- mart_dev.job_costs: (1, 3350), (2, 2650), (3, 1000), (4, 0). These match a hand computation from the workbook's job_runs: 67 min and 53 min at 50 cents, job 3 typed as 1000, job 4 with no runs as 0.
- mart_dev.team_runs: data 4, finance 5, web 0. These match the 9 runs in job_runs.
- admin/sent.csv records two creates and two writes.
- project.check() now lists only the CONVERSION notes, which the notebook says block nothing.

Points to note:
- Copilot's job_costs Hive hard-codes the rate as 50, the value in Parameters, rather than reading it by name. That matches file 11's rule for a Parameters value (typed in), so I left it. Changing the rate in Parameters will not change this table.
- No conflict with existing tables: mart_dev and team_prod were empty.

Where things are (absolute paths):
- Project: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E4-1\my_work\mart_project
- Hive saved: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E4-1\my_work\mart_project\admin\workflows\convert\finished\costs
- Table folders: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-E4-1\my_work\mart_project\tables\mart_dev__job_costs and ...\mart_dev__team_runs

Nothing in _loop was read or changed. Nothing was written to main/ except the Toolbox copy I made in my_work.
