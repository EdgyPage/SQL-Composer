"""Small helpers for editing a notebook's code cells in place, in Jupyter's JSON layout."""
import json
import sys
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, nb):
    text = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def code_cells(nb):
    return [c for c in nb["cells"] if c["cell_type"] == "code"]


def set_source(cell, text):
    lines = text.splitlines(keepends=True)
    cell["source"] = lines


if __name__ == "__main__":
    path, index, new_text_file = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    nb = load(path)
    cell = code_cells(nb)[index - 1]
    set_source(cell, Path(new_text_file).read_text(encoding="utf-8"))
    save(path, nb)
    print(f"set code cell {index} of {path}")
