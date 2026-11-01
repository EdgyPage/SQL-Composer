import json, sys
path = sys.argv[1]
raw = open(path, encoding="utf-8").read()
nb = json.loads(raw)
hits = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if src.startswith("NAME = ''"):
        lines = src.split("\n")
        new = []
        for line in lines:
            if line.startswith("NAME = "):
                line = "NAME = 'team_fails'  # the batch's name, plain lowercase, such as \"weekly\" (or, for the last cell alone, a list of batches converted already)"
            elif line.startswith("FILES = "):
                line = "FILES = ['weekly_fails.hql']  # the scripts' files, from this folder, such as [\"daily.hql\"], or [] to read HIVE"
            elif line.startswith("RENAME = "):
                line = "RENAME = {\"mart.team_fails\": \"team_fails\"}  # a name of your own for a table's copy in dev, by the table's full name, such as {\"mart.team_fails\": \"team_fails\"} for mart_dev.team_fails: left out, a copy is <table>_<its database>, such as mart_dev.team_fails_mart"
            new.append(line)
        src = "\n".join(new)
        cell["source"] = src.splitlines(keepends=True)
        hits += 1
assert hits == 1, hits
out = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
open(path, "w", encoding="utf-8", newline="\n").write(out)
print("names cell filled")
