DONE: Copied the three mart tables from weekly.hql into mart_dev (named as their originals), checked each against its original, and promoted them to team_prod with the Toolbox. Each table's folder is /data/team/mart_dev.db/<name> in dev and /data/team/team_prod.db/<name> in prod. The originals were not touched.

What I did, in order:
1. Made the Project at my_work\team_project (Toolbox copied in, project.start() run from start.ipynb, which I wrote by hand because Jupyter can't open here). warehouse.py now does sys.path.append on the work folder and `from team_connection import conn`.
2. Saved from_your_team\weekly.hql, unchanged, as admin\workflows\convert\weekly.hql. Filled the convert names cell (NAME "weekly", FILES ["weekly.hql"], DATABASE "mart", RENAME to the three bare names) and admin\databases.py (DEV "mart_dev", PROD "team_prod"). Ran the convert step: 3 Saved tables, the failed_runs staging table folded. Answered each table's only open Decision (location) in the decisions cell, then ran write_decisions.
3. Created, then wrote the three dev tables. compare_batch passed on dt 2026-09-24 (the latest Partition both hold) and I also ran it on dt 2026-09-23. Each of the 2 Partitions passed for all three tables, and the batch moved to admin\workflows\convert\finished\weekly\.
4. Promoted the three dev tables to team_prod (names kept, locations filled in by promote as /data/team/team_prod.db/<name>, which is correct). Created them, then wrote them. Refreshed the Reference sheet.
5. Checked: each dev and prod table's rows equal the original mart table's (3, 6 and 2 rows, all equal). project.check() names no open step.

Paths:
- Project: C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-H1-1\my_work\team_project
- Convert notebook: ...\my_work\team_project\admin\workflows\convert\convert.ipynb (batch in ...\admin\workflows\convert\finished\weekly\)
- Promote notebook: ...\my_work\team_project\admin\workflows\promote\promote.ipynb
- Compare results: ...\my_work\team_project\tables\mart_dev__team_fails\conversion\compare.md (and the same under mart_dev__job_runs_counted and mart_dev__job_fails_counted)
- Admin log and sent log: ...\my_work\team_project\admin\admin_log.md and ...\my_work\team_project\admin\sent.csv

Left open, on purpose: the TODO lines in the Table references (the "what one row is" line, and does_not_add_up=[] in each of references\mart_dev__*.py and references\team_prod__*.py). The convert docs say these wait on nothing. Also, the loose copy of weekly.hql remains in admin\workflows\convert\, beside the finished copy.

Usability observations from the docs and runner:
- The runner's --cells numbers count code cells, not the steps' numbers. I first ran --cells 10 meaning the create step (it was do_next, which changed nothing). The create step was code cell 6. Only --list gives the mapping, and the notebook text never says which cell number a step uses.
- Nothing in the README says where the Project folder goes relative to the work folder or what to call it. I chose my_work\team_project.
- The step to create start.ipynb is "made by you, in Jupyter". With no Jupyter, I wrote the notebook JSON by hand. The runner handled it fine.
- The convert how-to's compare step only checks the latest Partition. Checking another one needs a separate compare_batch call with partition=, which the docs mention, but I had to find it myself.
