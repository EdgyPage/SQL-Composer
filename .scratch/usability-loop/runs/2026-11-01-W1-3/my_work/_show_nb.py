import json, sys
nb = json.load(open(sys.argv[1], encoding="utf-8"))
for i, c in enumerate(nb["cells"]):
    print(f"=== cell {i} [{c['cell_type']}]")
    print("".join(c["source"]))
