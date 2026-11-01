"""Step 2's check: SHOW PARTITIONS on the Saved table, through the Project's warehouse.py."""
import sys

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W5-1\my_project")
from warehouse import query  # noqa: E402

frame = query("SHOW PARTITIONS mart_dev.runs_per_day")
print(frame.to_string())
print("rows:", len(frame))
