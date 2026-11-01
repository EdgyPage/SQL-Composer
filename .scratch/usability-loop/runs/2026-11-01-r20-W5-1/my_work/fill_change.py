"""Fill in the change_a_saved_table names cell and step 1's change, in the notebook's JSON."""
import json
from pathlib import Path

NB = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W5-1\my_project\admin\workflows\change_a_saved_table\change_a_saved_table.ipynb")

nb = json.loads(NB.read_text(encoding="utf-8"))
edits = {
    "TABLE = ''  # the Saved table to change, such as \"mart.daily_job_runs\"":
        "TABLE = \"mart_dev.runs_per_day\"  # the Saved table to change, such as \"mart.daily_job_runs\"",
    "change = admin.drop_partitions(table, where=...)  # or another: help(admin)":
        "change = admin.drop_partitions(table, where=equals(table.dt, \"2026-09-24\"))  # or another: help(admin)",
}
done = set()
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    text = "".join(cell["source"])
    for old, new in edits.items():
        if old in text:
            text = text.replace(old, new)
            done.add(old)
    lines = text.splitlines(keepends=True)
    cell["source"] = lines

missing = set(edits) - done
assert not missing, missing
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("ok")
