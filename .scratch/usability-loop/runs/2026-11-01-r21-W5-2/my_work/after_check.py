"""Read-only checks after the change: the partitions left, and what project.check() says."""
import os
import sys
from pathlib import Path

PROJECT = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r21-W5-2\my_project")
sys.path.insert(0, str(PROJECT))
os.chdir(PROJECT)

from sqlglot_composer import project  # noqa: E402
from warehouse import query  # noqa: E402

print(query("SHOW PARTITIONS mart_dev.runs_per_day"))
print("--- project.check()")
print(project.check())
