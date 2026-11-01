import json, sys
path = sys.argv[1]
nb = json.load(open(path, encoding="utf-8"))
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = cell["source"]
    if src and src[0].startswith("DECISIONS = {}"):
        hits += 1
        cell["source"] = [
            'DECISIONS = {"mart_dev.team_fails": {"location": "/data/team/mart_dev.db/team_fails"}}  # your answer to each open Decision, by the table\'s name as\n',
        ] + src[1:]
        print("".join(cell["source"]))
assert hits == 1, hits
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("saved")
