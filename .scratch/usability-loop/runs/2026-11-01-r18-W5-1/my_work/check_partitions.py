"""Run SHOW PARTITIONS on mart_dev.runs_per_day through the Project's warehouse.py."""
import sys

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W5-1\my_project")
from warehouse import query  # noqa: E402

print(query("SHOW PARTITIONS mart_dev.runs_per_day").to_string())
