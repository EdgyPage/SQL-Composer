import json, pathlib
p = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-09-W1-2/my_work/team_project/admin/workflows/convert/convert.ipynb")
nb = json.loads(p.read_text(encoding="utf-8"))
src = nb["cells"][2]["source"]
hit = [i for i, l in enumerate(src) if l.startswith("PARTITIONS = [])")  or l.startswith("PARTITIONS = []")]
assert len(hit) == 1, hit
src[hit[0]] = src[hit[0]].replace("PARTITIONS = []", "PARTITIONS = [{\"dt\": \"2026-09-23\"}]", 1)
p.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(src[hit[0]][:90])
