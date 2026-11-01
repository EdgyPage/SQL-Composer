"""Set one code cell's source in a notebook, keeping the rest of the file as it was."""
import json
import sys
from pathlib import Path


def set_cell(path, index, text):
    p = Path(path)
    nb = json.loads(p.read_text(encoding="utf-8"))
    lines = text.splitlines(keepends=True)
    nb["cells"][index]["source"] = lines
    p.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    set_cell(sys.argv[1], int(sys.argv[2]), Path(sys.argv[3]).read_text(encoding="utf-8"))
