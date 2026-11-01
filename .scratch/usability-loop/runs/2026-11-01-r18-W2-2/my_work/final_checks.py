import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W2-2\my_work\project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

from sqlglot_composer import check_table_reference, project  # noqa: E402
from references import mart_dev  # noqa: E402
from warehouse import query  # noqa: E402

print(project.check())
print("---")
print(check_table_reference(mart_dev.runs_per_day, query=query))
print("---")
print(query("SELECT job_id, runs, dt FROM mart_dev.runs_per_day ORDER BY dt, job_id"))
