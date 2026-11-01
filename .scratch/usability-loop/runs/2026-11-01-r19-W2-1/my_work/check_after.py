import sys
sys.path.insert(0, "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r19-W2-1/my_work/mart_project")
from warehouse import query
from sqlglot_composer import project
print(query("SELECT * FROM mart_dev.runs_per_day ORDER BY dt, job_id"))
print(query("SHOW PARTITIONS mart_dev.runs_per_day"))
print(project.check())
