import os
import sys

PROJECT = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W1-3\my_work\team_project"
os.chdir(PROJECT)
sys.path.insert(0, PROJECT)

from sqlglot_composer import project  # noqa: E402

print(project.start())
