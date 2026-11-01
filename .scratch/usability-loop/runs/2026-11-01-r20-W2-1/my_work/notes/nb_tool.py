"""Small helper: list or set the source of a notebook's code cells, keeping its JSON layout."""
import json
import sys
from pathlib import Path


def load(path):
    raw = Path(path).read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    return json.loads(raw), newline


def save(path, nb, newline):
    text = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
    Path(path).write_bytes(text.replace("\n", newline).encode("utf-8"))


def source_lines(text):
    lines = text.splitlines(keepends=True)
    return lines


def code_indexes(nb):
    return [i for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"]


if __name__ == "__main__":
    path = sys.argv[1]
    nb, newline = load(path)
    if sys.argv[2] == "roundtrip":
        save(path + ".rt", nb, newline)
    elif sys.argv[2] == "set":
        # set <code cell number from 1> <file with the new text>
        number = int(sys.argv[3])
        text = Path(sys.argv[4]).read_text(encoding="utf-8")
        index = code_indexes(nb)[number - 1]
        nb["cells"][index]["source"] = source_lines(text)
        save(path, nb, newline)
        print(f"Set code cell {number} (notebook cell {index}).")
