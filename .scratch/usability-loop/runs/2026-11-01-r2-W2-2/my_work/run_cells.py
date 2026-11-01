"""Run chosen code cells of a notebook, in one namespace, from its folder (like run_notebook but chosen cells)."""
import json, os, sys, traceback
path = os.path.abspath(sys.argv[1])
wanted = [int(x) for x in sys.argv[2:]]
nb = json.load(open(path, encoding="utf-8"))
folder = os.path.dirname(path)
sys.path.insert(0, folder)
os.chdir(folder)
ns = {"__name__": "__main__"}
for i in wanted:
    src = "".join(nb["cells"][i]["source"])
    print(f"--- cell {i}")
    try:
        exec(compile(src, f"cell{i}", "exec"), ns)
    except Exception:
        traceback.print_exc(file=sys.stdout)
        print(f"--- stopped at cell {i}")
        sys.exit(1)
print("--- done")
