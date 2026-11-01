import json, pathlib, sys
nb_path = pathlib.Path(sys.argv[1])
nb = json.loads(nb_path.read_text(encoding="utf-8"))
ns = {"__name__": "__main__"}
for i in [int(a) for a in sys.argv[2:]]:
    exec("".join(nb["cells"][i]["source"]), ns)
