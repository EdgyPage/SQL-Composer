import json
from pathlib import Path

nb = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r18-W4-2\my_work\my_project\admin\workflows\references\references.ipynb")
data = json.loads(nb.read_text(encoding="utf-8"))
done = 0
for cell in data["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if src.startswith("TABLES = []"):
        new = src.replace("TABLES = []", 'TABLES = ["ops.jobs", "ops.run_alerts"]', 1)
        cell["source"] = new.splitlines(keepends=True)
        done += 1
print("changed", done)
nb.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
