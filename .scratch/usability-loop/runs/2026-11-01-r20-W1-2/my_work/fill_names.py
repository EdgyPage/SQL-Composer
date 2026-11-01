import json, sys
path = sys.argv[1]
nb = json.load(open(path, encoding="utf-8"))
edits = {
    "NAME = ": 'NAME = "weekly_fails"  # the batch\'s name, plain lowercase, such as "weekly" (or, for the last cell alone, a list of batches converted already)\n',
    "FILES = ": 'FILES = ["weekly_fails.hql"]  # the scripts\' files, from this folder, such as ["daily.hql"], or [] to read HIVE\n',
    "RENAME = ": 'RENAME = {"mart.team_fails": "team_fails"}  # a name of your own for a table\'s copy in dev, by the table\'s full name, such as {"mart.team_fails": "team_fails"} for mart_dev.team_fails: left out, a copy is <table>_<its database>, such as mart_dev.team_fails_mart\n',
}
done = set()
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = cell["source"]
    if not any(l.startswith("NAME = ") for l in src):
        continue
    new = []
    for line in src:
        for key, repl in edits.items():
            if line.startswith(key):
                new.append(repl)
                done.add(key)
                break
        else:
            new.append(line)
    cell["source"] = new
    print("".join(new))
assert done == set(edits), done
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("saved")
