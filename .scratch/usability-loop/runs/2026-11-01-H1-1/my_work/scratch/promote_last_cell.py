"""The promote notebook's last cell, run as its own script (my own wrapper); dry run first."""
import os, pathlib, sys
project_root = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-H1-1/my_work/project")
sys.path.insert(0, str(project_root))
os.chdir(project_root / "admin/workflows/promote")
from sqlglot_composer import project  # noqa
from warehouse import query, execute  # noqa
dry = "--dry" in sys.argv
print(project.run_workflow("promote", query=query, execute=execute, dry_run=dry))
