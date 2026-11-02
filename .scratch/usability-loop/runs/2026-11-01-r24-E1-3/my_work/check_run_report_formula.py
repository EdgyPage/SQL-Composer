from openpyxl import load_workbook
BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r24-E1-3"
tpl = load_workbook(f"{BASE}/main/copilot/formula_workbook.xlsx")
out = load_workbook(f"{BASE}/my_work/run_report_formula.xlsx")
for name in ["Steps", "Parameters", "Keys"]:
    a = [[c.value for c in r] for r in tpl[name].iter_rows()]
    b = [[c.value for c in r] for r in out[name].iter_rows()]
    print(name, "unchanged" if a == b else "CHANGED")
# expected figures from the raw rows, computed independently
ws = out["job_runs"]
rows = [[c.value for c in r] for r in ws.iter_rows(min_row=3, max_row=11)]
for job in (1, 2, 3):
    mine = [r for r in rows if r[1] == job]
    runs = len(mine)
    failed = sum(1 for r in mine if r[2] == "FAILED")
    avg = sum(r[3] for r in mine) / runs
    print("job", job, "runs", runs, "failed", failed, "avg", round(avg, 4))
