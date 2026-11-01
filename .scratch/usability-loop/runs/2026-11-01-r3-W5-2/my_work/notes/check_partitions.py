"""Read the Check first line's SHOW PARTITIONS through the Project's warehouse.query."""
import sys

sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r3-W5-2\my_project")
from warehouse import query  # noqa: E402

result = query("SHOW PARTITIONS mart_dev.runs_per_day")
print(result.to_string())
