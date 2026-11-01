import sys
sys.path.insert(0, "/c/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-W3-3/my_work/project")
from warehouse import conn
df = conn.query("SHOW PARTITIONS ops.job_runs")
print(df.to_string())
