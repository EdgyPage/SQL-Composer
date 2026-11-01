import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W1-1\my_work\team_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

from warehouse import query

print(query("SELECT * FROM mart.team_fails LIMIT 5"))
print(query("DESCRIBE mart.team_fails"))
print(query("SELECT * FROM ops.job_owners LIMIT 3"))
print(query("DESCRIBE ops.job_owners"))
print(query("DESCRIBE ops.job_runs"))
