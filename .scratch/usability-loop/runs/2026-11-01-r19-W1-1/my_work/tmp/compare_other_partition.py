import pathlib
import sys
import os

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-W1-1\my_work"
os.chdir(os.path.join(PROJECT, "admin", "workflows", "convert"))
sys.path.insert(0, PROJECT)

from sqlglot_composer import admin, hive_settings, project, run_execute, run_query, show_hive
from warehouse import query, execute

NAME = "team_fails"
print(project.compare_batch(NAME, query=query, partition={"dt": "2026-09-23"}))
