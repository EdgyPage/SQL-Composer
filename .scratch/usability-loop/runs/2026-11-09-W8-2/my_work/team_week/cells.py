import json, sys
nb = json.load(open(sys.argv[1], encoding="utf-8"))
n = 0
for c in nb["cells"]:
    if c["cell_type"] == "code":
        n += 1
        print(f"=== code cell {n} tags={c.get('metadata',{}).get('tags',[])}")
    else:
        print(f"--- {c['cell_type']} cell")
    print("".join(c["source"]))
    print()
