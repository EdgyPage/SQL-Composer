import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    nb = json.load(f)
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
names, step1 = code[1], code[2]
assert "".join(names["source"]).startswith("TABLE = ''"), names["source"]
assert "change = admin.drop_partitions(table, where=...)" in "".join(step1["source"])
names["source"] = ['TABLE = "mart_dev.runs_per_day"  # the Saved table to change, such as "mart.daily_job_runs"']
src = "".join(step1["source"]).replace("where=...)", 'where=equals(table.dt, "2026-09-24"))', 1)
step1["source"] = src.splitlines(keepends=True)
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("filled")
