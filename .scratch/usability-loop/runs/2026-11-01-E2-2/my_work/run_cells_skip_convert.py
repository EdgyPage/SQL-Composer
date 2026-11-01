import json, sys, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("runner", "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-E2-2/run_notebook.py")
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
nb = Path(sys.argv[1]).resolve()
skip = {int(x) for x in sys.argv[2].split(',')} if len(sys.argv) > 2 else set()
ns = {"__name__": "__main__"}
cells = [c for c in json.loads(nb.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code"]
with contextlib.chdir(nb.parent):
    for n, c in enumerate(cells, 1):
        if n in skip:
            print(f"--- cell {n} skipped"); continue
        print(f"--- cell {n}")
        try:
            runner.run_cell("".join(c["source"]), ns)
        except Exception as e:
            import traceback; traceback.print_exc(file=sys.stdout)
            print(f"--- stopped at cell {n}"); sys.exit(1)
print("--- every cell ran")
