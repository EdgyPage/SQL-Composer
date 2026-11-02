import sys, os
PROJECT = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E1-1/my_work/run_report_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)
from warehouse import query, execute
print(query("SHOW TABLES IN mart_dev").to_string())
print(query("SELECT * FROM mart_dev.job_run_report ORDER BY job_id").to_string())
d = query("DESCRIBE FORMATTED mart_dev.job_run_report")
print(d[d.iloc[:,0].astype(str).str.contains("Location|Table Type", regex=True)].to_string())
