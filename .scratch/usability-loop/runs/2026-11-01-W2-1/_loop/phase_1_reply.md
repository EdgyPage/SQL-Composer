DONE: Made mart_dev.runs_per_day with the Toolbox and wrote it in dev: 6 rows, one per job and day, job_id, runs and dt, partitioned by dt, at /data/team/mart_dev.db/runs_per_day. Matches a plain SQL count.

Friction it named: from_your_team/ absent (none given for W2); run_notebook.py fails with a relative notebook path (it chdirs first); project.start() and do_next() print nothing from a plain script; add_references leaves key=None and does_not_add_up=[] as TODOs, and nothing says how to pick a Key (found it from check_key's error).
