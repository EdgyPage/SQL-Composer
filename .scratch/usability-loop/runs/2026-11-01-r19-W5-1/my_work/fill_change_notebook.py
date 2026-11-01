import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
raw = path.read_text(encoding="utf-8")
nb = json.loads(raw)
edits = {
    'TABLE = \'\'  # the Saved table to change, such as "mart.daily_job_runs"':
        'TABLE = "mart_dev.runs_per_day"  # the Saved table to change, such as "mart.daily_job_runs"',
    "change = admin.drop_partitions(table, where=...)  # or another: help(admin)":
        'change = admin.drop_partitions(table, where=equals(table.dt, "2026-09-24"))  # or another: help(admin)',
}
done = set()
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    lines = cell["source"]
    text = "".join(lines)
    for old, new in edits.items():
        if old in text:
            text = text.replace(old, new)
            done.add(old)
            cell["source"] = text.splitlines(keepends=True)
assert done == set(edits), done
out = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
path.write_text(out, encoding="utf-8")
print("edited", len(done), "lines")
