import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W1-1\my_work\team_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

from sqlglot_composer import project

print(project.start())
