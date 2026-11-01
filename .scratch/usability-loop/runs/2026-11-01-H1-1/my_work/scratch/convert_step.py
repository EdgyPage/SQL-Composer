"""Step 1 of the convert Workflow, the convert cell run with rename= (my own wrapper)."""
import os, pathlib, sys
project_root = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-H1-1/my_work/project")
sys.path.insert(0, str(project_root))
os.chdir(project_root / "admin/workflows/convert")
from sqlglot_composer import admin, hive_settings, project, run_execute, run_query, show_hive  # noqa
from warehouse import query, execute  # noqa
NAME = "weekly"
FILES = ["weekly.hql"]
HIVE = None
DATABASE = "mart"
STAGING = {}
RENAME = {"mart.team_fails": "team_fails", "mart.job_runs_counted": "job_runs_counted",
          "mart.job_fails_counted": "job_fails_counted"}
print(project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,
                      staging=STAGING, rename=RENAME))
