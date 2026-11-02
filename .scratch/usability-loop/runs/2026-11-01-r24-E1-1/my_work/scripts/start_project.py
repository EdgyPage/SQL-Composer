import sys
import os

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r24-E1-1\my_work\run_report_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

from sqlglot_composer import project

print(project.start())
