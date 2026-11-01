"""Scratch helper: show a notebook's cells, set one cell's source, or run cells in order up to one.

  nb.py show NB
  nb.py set NB INDEX TEXTFILE      (INDEX is the cell's position in the notebook, as show prints it)
  nb.py run NB UPTO_INDEX          (runs each code cell at a position <= UPTO_INDEX, in one namespace, cwd = notebook's folder)
"""
import contextlib
import json
import sys
import traceback
from pathlib import Path

WORK = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-W2-1\my_work")
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(WORK.parent))
import run_notebook  # the usability loop's runner, which runs each cell as Jupyter does


def load(nb_path):
    return json.loads(Path(nb_path).read_text(encoding="utf-8"))


def save(nb_path, nb):
    Path(nb_path).write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def to_lines(text):
    lines = text.splitlines(keepends=True)
    return lines


def main(argv):
    cmd, nb_path = argv[0], Path(argv[1]).resolve()
    if cmd == "show":
        nb = load(nb_path)
        for i, c in enumerate(nb["cells"]):
            print(f"--- [{i}] {c['cell_type']}")
            print("".join(c["source"]))
        return 0
    if cmd == "set":
        index, text_file = int(argv[2]), Path(argv[3])
        nb = load(nb_path)
        nb["cells"][index]["source"] = to_lines(text_file.read_text(encoding="utf-8"))
        save(nb_path, nb)
        print(f"set cell {index}")
        return 0
    if cmd == "run":
        upto = int(argv[2])
        nb = load(nb_path)
        namespace = {"__name__": "__main__"}
        sys.path.insert(0, str(nb_path.parent))
        with contextlib.chdir(nb_path.parent):
            for i, c in enumerate(nb["cells"]):
                if c["cell_type"] != "code" or i > upto:
                    continue
                source = "".join(c["source"])
                print(f"--- cell [{i}]")
                try:
                    run_notebook.run_cell(source, namespace)
                except Exception:
                    traceback.print_exc(file=sys.stdout)
                    print(f"--- stopped at cell [{i}]")
                    return 1
        print("--- ran up to", upto)
        return 0
    if cmd == "cells":
        # run only the listed cell positions, in order, in one namespace, after the imports
        wanted = [int(x) for x in argv[2].split(",")]
        nb = load(nb_path)
        namespace = {"__name__": "__main__"}
        sys.path.insert(0, str(nb_path.parent))
        with contextlib.chdir(nb_path.parent):
            for i in wanted:
                c = nb["cells"][i]
                source = "".join(c["source"])
                print(f"--- cell [{i}]")
                try:
                    run_notebook.run_cell(source, namespace)
                except Exception:
                    traceback.print_exc(file=sys.stdout)
                    print(f"--- stopped at cell [{i}]")
                    return 1
        print("--- ran", wanted)
        return 0
    print("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
