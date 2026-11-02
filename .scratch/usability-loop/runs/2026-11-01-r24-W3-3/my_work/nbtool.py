"""Small helper: show or set the source of one code cell of a notebook, keeping its layout.

    python nbtool.py show  <notebook>
    python nbtool.py set   <notebook> <code cell number, from 1> <file holding the new text>
"""
import json
import sys


def load(path):
    with open(path, encoding="utf-8", newline="") as f:
        return json.loads(f.read())


def save(path, nb):
    text = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)


def code_cells(nb):
    return [c for c in nb["cells"] if c["cell_type"] == "code"]


def main(argv):
    if argv[0] == "show":
        nb = load(argv[1])
        for n, c in enumerate(code_cells(nb), 1):
            print(f"--- code cell {n}")
            print("".join(c["source"]))
        return 0
    if argv[0] == "set":
        path, number, text_file = argv[1], int(argv[2]), argv[3]
        with open(text_file, encoding="utf-8") as f:
            text = f.read()
        nb = load(path)
        cell = code_cells(nb)[number - 1]
        lines = text.splitlines(keepends=True)
        if lines and not lines[-1].endswith("\n"):
            lines[-1] = lines[-1]
        cell["source"] = lines
        save(path, nb)
        print(f"set code cell {number} of {path}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
