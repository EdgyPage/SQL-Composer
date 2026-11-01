"""Fill in the names cell and the step 1 decision of change_a_saved_table, keeping the file's format."""
import json
from pathlib import Path

NB = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r19-W5-3\my_project\admin\workflows\change_a_saved_table\change_a_saved_table.ipynb")

raw = NB.read_bytes().decode("utf-8")
nb = json.loads(raw)

def cell_text(cell):
    return "".join(cell["source"])

def set_source(cell, text):
    lines = text.splitlines(keepends=True)
    cell["source"] = lines

changed = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    text = cell_text(cell)
    if text.startswith("TABLE = ''"):
        new = text.replace("TABLE = ''", 'TABLE = "mart_dev.runs_per_day"', 1)
        set_source(cell, new)
        changed += 1
    elif text.startswith("import pathlib") or text.startswith("from sqlglot_composer import between") or text.startswith("change = admin") or "change = admin.drop_partitions(table, where=...)" in text:
        pass
    if "change = admin.drop_partitions(table, where=...)" in text:
        new = text.replace("where=...)  # or another", 'where=equals(table.dt, "2026-09-24"))  # or another', 1)
        set_source(cell, new)
        changed += 1

assert changed == 2, changed
out = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
out = out.replace("\n", "\r\n")
NB.write_bytes(out.encode("utf-8"))
print("written")
