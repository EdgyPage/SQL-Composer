import json, sys
path = sys.argv[1]
nb = json.loads(open(path, encoding="utf-8").read())
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "".join(cell["source"]).startswith("DECISIONS = {}"):
        cell["source"] = [
            'DECISIONS = {"mart_dev.team_fails": {"location": "/data/team/mart_dev.db/team_fails"}}'
            '  # your answer to each open Decision, by the table\'s name as\n',
            '# project.check() writes it, such as\n',
            '# {"mart_dev.weekly": {"location": "/data/team/mart_dev.db/weekly",\n',
            '#                      "key": ["job_id"], "types": {"fails": "bigint"}}}\n',
            '# "key": None says no columns name one row. project.check() names each one open;\n',
            '# a Key proposed from a query is made, but an answer here changes it',
        ]
        hits += 1
assert hits == 1, hits
open(path, "w", encoding="utf-8", newline="\r\n").write(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print("decisions cell filled")
