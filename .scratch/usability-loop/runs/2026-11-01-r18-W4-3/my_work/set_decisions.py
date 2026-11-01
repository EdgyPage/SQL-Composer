import json, pathlib, sys
nb = pathlib.Path(sys.argv[1])
data = json.loads(nb.read_text(encoding="utf-8"))
hits = 0
for cell in data["cells"]:
    if cell["cell_type"] == "code" and "".join(cell["source"]).startswith("DECISIONS = {}"):
        src = "".join(cell["source"])
        new = src.replace(
            "DECISIONS = {}  # your answer to each open Decision, by the table's name as\n",
            'DECISIONS = {"ops.jobs": {"key": ["job_id"]}, "ops.run_alerts": {"key": ["alert_id"]}}\n'
            "# your answer to each open Decision, by the table's name as\n", 1)
        assert new != src
        cell["source"] = new.splitlines(keepends=True)
        hits += 1
assert hits == 1, hits
nb.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("decisions cell set")
