import os, sys
PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-E3-3\my_work\daily_runs_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)
from sqlglot_composer import project
print(project.start())
