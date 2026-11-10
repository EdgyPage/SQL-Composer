import json, pathlib
p = pathlib.Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-09-W1-2/my_work/team_project/admin/workflows/convert/convert.ipynb")
nb = json.loads(p.read_text(encoding="utf-8"))
c1 = nb["cells"][1]["source"]
assert sum(1 for l in c1 if l.startswith("# connect(your_connection)")) == 1
new1 = []
for line in c1:
    if line.startswith("# connect(your_connection)"):
        new1 += [
            'sys.path.append("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-09-W1-2")\n',
            "from team_connection import conn\n",
            "connect(conn)\n",
        ]
    else:
        new1.append(line)
nb["cells"][1]["source"] = new1
repl = {
    "NAME = ''": "NAME = 'team_fails'",
    "FILES = []": "FILES = ['weekly_fails.hql']",
    "RENAME = {}": 'RENAME = {"mart.team_fails": "team_fails"}',
}
out = []
for line in nb["cells"][2]["source"]:
    for k, v in repl.items():
        if line.startswith(k):
            line = v + line[len(k):]
            break
    out.append(line)
nb["cells"][2]["source"] = out
p.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("".join(new1))
print("".join(out[:3]))
print([l for l in out if l.startswith("RENAME")])
