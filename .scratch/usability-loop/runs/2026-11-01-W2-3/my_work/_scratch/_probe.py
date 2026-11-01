import sys, pathlib, os
here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here.parents[1]))
sys.path.insert(0, str(here))
os.chdir(here)
from sqlglot_composer import *
from sqlglot_composer import project
from warehouse import query
from references import ops
import pandas as pd
pd.set_option("display.width", 200)
print(check_key(ops.job_runs, query=query, where=equals(ops.job_runs.dt, "2026-09-23")))
print(check_key(ops.job_runs, query=query, where=equals(ops.job_runs.dt, "2026-09-24")))
print(query("SELECT dt, job_id, COUNT(*) AS n FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY dt, job_id ORDER BY dt, job_id"))
print(query("SELECT dt, COUNT(*) AS n, COUNT(DISTINCT run_id) AS d, COUNT(job_id) AS nj, SUM(CASE WHEN job_id IS NULL THEN 1 ELSE 0 END) AS nulljobs FROM ops.job_runs GROUP BY dt"))
