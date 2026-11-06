import json, sys
nb = json.load(open(sys.argv[1], encoding="utf-8"))
n = 0
for i, c in enumerate(nb["cells"]):
    if c["cell_type"] == "code":
        n += 1
        print(f"---- cell {i} (code #{n})")
    else:
        print(f"---- cell {i} ({c['cell_type']})")
    print("".join(c["source"]))
