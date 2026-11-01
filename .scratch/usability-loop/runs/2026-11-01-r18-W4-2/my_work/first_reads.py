import sys, os
P = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W4-2\my_work\my_project"
sys.path.insert(0, P)
os.chdir(P)
from sqlglot_composer import statement, SELECT, FROM, WHERE, equals, between, run_query, show_hive, to_hive
from references import ops
from warehouse import query

jobs = ops.jobs
run_alerts = ops.run_alerts

# Every job, one row each
all_jobs = statement(
    SELECT(jobs.job_id, jobs.job_name, jobs.team, jobs.region),
    FROM(jobs),
)
print(show_hive(all_jobs))
print(run_query(all_jobs, query))
print("=====")

# Alerts of high severity on 2026-09-24, the partition that holds them
high_alerts = statement(
    SELECT(run_alerts.alert_id, run_alerts.run_id, run_alerts.severity, run_alerts.dt),
    FROM(run_alerts),
    WHERE(equals(run_alerts.severity, "high"),
          equals(run_alerts.dt, "2026-09-24")),
)
print(show_hive(high_alerts))
print(run_query(high_alerts, query))
