import json, sys
path, index, text = sys.argv[1], int(sys.argv[2]), sys.argv[3]
nb = json.load(open(path, encoding="utf-8"))
lines = text.splitlines(keepends=True)
nb["cells"][index]["source"] = lines
json.dump(nb, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(path, "a", encoding="utf-8").write("\n")
print("set cell", index, "of", path)
