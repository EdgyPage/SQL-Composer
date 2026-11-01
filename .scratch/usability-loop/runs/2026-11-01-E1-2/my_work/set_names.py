import json, sys
from pathlib import Path
# usage: set_names.py NOTEBOOK CELL_INDEX  (new source read from stdin)
path, idx = Path(sys.argv[1]), int(sys.argv[2])
nb = json.loads(path.read_text(encoding="utf-8"))
text = sys.stdin.read()
lines = text.split("\n")
nb["cells"][idx]["source"] = [l + "\n" for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("set cell", idx, "of", path.name)
