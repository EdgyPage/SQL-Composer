import json, pathlib, sys
nb = pathlib.Path(sys.argv[1])
data = json.loads(nb.read_text(encoding="utf-8"))
old = 'TABLES = []  # the tables, by their names in the warehouse, such as ["mart.daily_job_runs"]'
new = 'TABLES = ["ops.jobs", "ops.run_alerts"]  # the tables, by their names in the warehouse, such as ["mart.daily_job_runs"]'
hits = 0
for cell in data["cells"]:
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        if src == old:
            cell["source"] = [new]
            hits += 1
assert hits == 1, hits
nb.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("names cell set")
