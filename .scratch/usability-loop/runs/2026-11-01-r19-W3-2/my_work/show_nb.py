import json, sys
nb = json.load(open(sys.argv[1], encoding="utf-8"))
for i, c in enumerate(nb["cells"]):
    print(f"--- [{c['cell_type']}] cell {i}")
    print("".join(c["source"]))
