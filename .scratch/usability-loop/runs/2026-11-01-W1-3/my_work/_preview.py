import sys, json, contextlib
from pathlib import Path
sys.path.insert(0, r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-W1-3")
import run_notebook
nb = Path("mart_dev__team_fails.ipynb").resolve()
cells = json.loads(nb.read_text(encoding="utf-8"))["cells"]
ns = {"__name__": "__main__"}
with contextlib.chdir(nb.parent):
    for i in (1, 2):
        run_notebook.run_cell("".join(cells[i]["source"]), ns)
    import pandas as pd
    pd.set_option("display.width", 200)
    from warehouse import query
    print("PREVIEW:")
    print(ns["run_query"](ns["preview"](), query))
    print("ORIGINAL:")
    print(query("SELECT team, fails, dt FROM mart.team_fails ORDER BY dt, team"))
