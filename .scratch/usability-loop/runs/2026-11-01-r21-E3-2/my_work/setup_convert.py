import pathlib

PROJECT = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r21-E3-2/my_work/mart_project")
WORK = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r21-E3-2"

p = PROJECT / "warehouse.py"
s = p.read_text(encoding="utf-8")
old = "conn = example_database\n"
assert s.count(old) == 1
new = f'import sys\n\nsys.path.append(r"{WORK}")\nfrom team_connection import conn\n'
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")

d = PROJECT / "admin" / "databases.py"
t = d.read_text(encoding="utf-8")
t = t.replace('DEV = "<DEV_DATABASE>"', 'DEV = "mart_dev"').replace('PROD = "<PROD_DATABASE>"', 'PROD = "team_prod"')
d.write_text(t, encoding="utf-8")

hql = """WITH CleanRuns AS (
  SELECT run_id, job_id, status, duration_mins, avg_retry_secs, dt
  FROM ops.job_runs
  WHERE status IS NOT NULL AND status <> 'TEST'
)
SELECT d.dt,
  COALESCE(c.runs, 0) AS runs,
  COALESCE(c.total_duration_mins, 0) AS total_duration_mins
FROM (SELECT '2026-09-23' AS dt UNION ALL SELECT '2026-09-24') d
LEFT JOIN (
  SELECT dt, COUNT(*) AS runs, SUM(duration_mins) AS total_duration_mins
  FROM CleanRuns
  GROUP BY dt
) c
  ON d.dt = c.dt
"""
(PROJECT / "admin" / "workflows" / "convert" / "daily_runs.hql").write_text(hql, encoding="utf-8")
print("ok")
