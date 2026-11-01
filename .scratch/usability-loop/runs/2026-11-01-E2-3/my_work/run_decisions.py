import os, sys
PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-E2-3\my_work\team_project"
sys.path.insert(0, PROJECT)
os.chdir(os.path.join(PROJECT, "admin", "workflows", "convert"))
from sqlglot_composer import admin, hive_settings, project, run_execute, run_query, show_hive
from warehouse import query, execute

NAME = "team_report"
DECISIONS = {"mart_dev.team_report": {"location": "/data/team/mart_dev.db/team_report",
                                      "key": ["team"],
                                      "types": {"team": "string", "runs": "bigint",
                                                "total_duration_mins": "bigint"}}}
print(project.write_decisions(DECISIONS))
print(project.check())
