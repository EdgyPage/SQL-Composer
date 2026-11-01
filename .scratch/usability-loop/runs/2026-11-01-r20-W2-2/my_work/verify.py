import sys
sys.path.insert(0, ".")
from warehouse import query
print(query("SHOW PARTITIONS mart_dev.runs_per_day"))
print(query("SELECT job_id, runs, dt FROM mart_dev.runs_per_day ORDER BY dt, job_id"))
