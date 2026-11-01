import os, sys
root = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W5-3\my_project"
os.chdir(os.path.join(root, "admin", "workflows", "change_a_saved_table"))
sys.path.insert(0, root)
from warehouse import query
print(query("SHOW PARTITIONS mart_dev.runs_per_day").to_string())
print(query("SELECT dt, COUNT(*) AS n FROM mart_dev.runs_per_day GROUP BY dt ORDER BY dt").to_string())
