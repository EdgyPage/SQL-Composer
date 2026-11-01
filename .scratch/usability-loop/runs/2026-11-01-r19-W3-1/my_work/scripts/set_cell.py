"""Set the source of one code cell of a notebook, by its code-cell number from 1,
keeping the file's CRLF line endings. Usage: set_cell.py NOTEBOOK NUMBER TEXTFILE"""
import json
import sys

nb_path, number, text_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
raw = open(nb_path, "rb").read().decode("utf-8")
nb = json.loads(raw)
new_text = open(text_path, encoding="utf-8").read()
code = [c for c in nb["cells"] if c["cell_type"] == "code"]
lines = new_text.splitlines(keepends=True)
code[number - 1]["source"] = lines
out = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
open(nb_path, "wb").write(out.replace("\n", "\r\n").encode("utf-8"))
print("set code cell", number, "of", nb_path)
