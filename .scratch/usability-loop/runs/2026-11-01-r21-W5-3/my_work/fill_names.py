"""Fill the names cell and step 1 of change_a_saved_table.ipynb, by editing its JSON text."""
import json
import sys
from pathlib import Path

nb_path = Path(sys.argv[1])
raw = nb_path.read_text(encoding="utf-8")
nb = json.loads(raw)

replacements = {
    "TABLE = ''  # the Saved table to change, such as \"mart.daily_job_runs\"":
        "TABLE = \"mart_dev.runs_per_day\"  # the Saved table to change, such as \"mart.daily_job_runs\"",
    "change = admin.drop_partitions(table, where=...)  # or another: help(admin)":
        "change = admin.drop_partitions(table, where=equals(table.dt, \"2026-09-24\"))  # or another: help(admin)",
}

count = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    new = src
    for old, repl in replacements.items():
        if old in new:
            new = new.replace(old, repl)
            count += 1
    if new != src:
        lines = new.splitlines(keepends=True)
        cell["source"] = lines

print("replaced", count)
new_raw = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
nb_path.write_text(new_raw, encoding="utf-8")
