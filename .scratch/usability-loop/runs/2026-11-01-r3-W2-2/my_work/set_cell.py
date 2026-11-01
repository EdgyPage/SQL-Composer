"""Set the source of one code cell of a notebook: set_cell.py notebook.ipynb CELL_NUMBER text_file"""
import json, sys
path, number, text_file = sys.argv[1], int(sys.argv[2]), sys.argv[3]
nb = json.load(open(path, encoding="utf-8"))
text = open(text_file, encoding="utf-8").read()
lines = text.splitlines(keepends=True)
nb["cells"][number - 1]["source"] = lines
with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")
print("set cell", number, "of", path)
