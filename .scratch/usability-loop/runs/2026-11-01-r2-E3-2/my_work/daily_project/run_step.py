import json, pathlib, sys
nb = json.loads(pathlib.Path("convert.ipynb").read_text(encoding="utf-8"))
ns = {"__name__": "__main__"}
for i in [int(a) for a in sys.argv[1:]]:
    exec("".join(nb["cells"][i]["source"]), ns)
print("ran cells", sys.argv[1:])
