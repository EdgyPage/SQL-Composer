"""Run the change_a_saved_table notebook's code cells in turn, stopping before the first cell
that sends (its run_execute or its run_workflow call), as a dry run for reading the Hive."""
import contextlib
import json
import os
import pathlib
import sys
import traceback

NB = pathlib.Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W5-3\my_project\admin\workflows\change_a_saved_table\change_a_saved_table.ipynb")
SENDS = ("run_execute(", "run_workflow(")

cells = [
    "".join(c["source"]) for c in json.loads(NB.read_text(encoding="utf-8"))["cells"]
    if c["cell_type"] == "code"
]
os.chdir(NB.parent)
namespace = {"__name__": "__main__"}
for number, source in enumerate(cells, 1):
    if any(word in source for word in SENDS):
        print(f"--- stopped before cell {number}: it sends")
        break
    print(f"--- cell {number}")
    try:
        exec(compile(source, f"cell{number}", "exec"), namespace)
    except Exception:
        traceback.print_exc(file=sys.stdout)
        print(f"--- stopped at cell {number}")
        break
