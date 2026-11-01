"""Run a notebook's code cells in turn, up to and including cell N (1-based, code cells only),
the way run_notebook.py does, so a Workflow's steps can be run one at a time."""
import sys
from pathlib import Path

RUNNER = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E1-3"
sys.path.insert(0, RUNNER)
from run_notebook import code_cells, run_cell  # noqa: E402


def main(argv):
    notebook = Path(argv[1]).resolve()
    upto = int(argv[2])
    skip = {int(n) for n in argv[3].split(",")} if len(argv) > 3 and argv[3] else set()
    sources = code_cells(notebook)
    namespace = {"__name__": "__main__"}
    import contextlib, traceback
    sys.path.insert(0, str(notebook.parent))
    with contextlib.chdir(notebook.parent):
        for number, source in enumerate(sources, 1):
            if number > upto:
                break
            if number in skip:
                print(f"--- cell {number} skipped (already done)")
                continue
            print(f"--- cell {number}")
            try:
                run_cell(source, namespace)
            except Exception:
                traceback.print_exc(file=sys.stdout)
                print(f"--- stopped at cell {number}")
                return 1
    print(f"--- ran cells 1 to {min(upto, len(sources))} of {len(sources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
