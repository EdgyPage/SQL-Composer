import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W2-2\my_work\project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

from warehouse import query  # noqa: E402

print(query("SELECT job_id, dt, COUNT(*) AS runs FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY job_id, dt ORDER BY job_id, dt"))
print(query("SELECT dt, COUNT(*) AS n, COUNT(DISTINCT run_id) AS d FROM ops.job_runs WHERE dt BETWEEN '2026-09-23' AND '2026-09-24' GROUP BY dt"))
print(query("SELECT dt, COUNT(*) AS n FROM ops.job_runs GROUP BY dt ORDER BY dt"))
