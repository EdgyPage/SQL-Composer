from pathlib import Path
import json

nb = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W4-1\my_work\my_project\admin\workflows\references\references.ipynb")
raw = nb.read_bytes()
old = b'"TABLES = []  # the tables, by their names in the warehouse, such as [\\"mart.daily_job_runs\\"]"'
new = b'"TABLES = [\\"ops.jobs\\", \\"ops.run_alerts\\"]  # the tables, by their names in the warehouse, such as [\\"mart.daily_job_runs\\"]"'
assert raw.count(old) == 1, raw.count(old)
raw = raw.replace(old, new)
nb.write_bytes(raw)
cells = json.loads(nb.read_text(encoding="utf-8"))["cells"]
print([ "".join(c["source"]) for c in cells if c["cell_type"] == "code"][1])
