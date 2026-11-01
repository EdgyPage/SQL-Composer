import openpyxl
BASE = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r3-E2-2"
out = openpyxl.load_workbook(BASE + "/my_work/team_report_formula.xlsx")
src = openpyxl.load_workbook(BASE + "/from_your_team/team_report.xlsx")
for ws in out.worksheets:
    print("=== SHEET", ws.title, ws.dimensions, {n: ws.tables[n].ref for n in ws.tables})
    for row in ws.iter_rows():
        vals = [c.value for c in row]
        if any(v is not None for v in vals):
            print("  ", row[0].row, vals)
# Data check: each raw value copied matches the source
def grid(ws, r1, r2, c2):
    return [[ws.cell(row=r, column=c).value for c in range(1, c2 + 1)] for r in range(r1, r2 + 1)]
print("Jobs data matches:", grid(src["Jobs"], 2, 5, 4) == grid(out["Jobs"], 3, 6, 4))
print("Runs raw data matches:", grid(src["Runs"], 2, 10, 6) == grid(out["Runs"], 3, 11, 6))
print("Teams names match:", [src["Teams"].cell(row=r, column=1).value for r in range(2, 5)] == [out["Teams"].cell(row=r, column=1).value for r in range(2, 5)])
print("Steps sheet intact:", out["Steps"]["A1"].value, "|", out["Steps"].max_row, "rows")
print("Parameters empty:", [[c.value for c in r] for r in out["Parameters"].iter_rows(min_row=1, max_row=2, max_col=2)])
print("Keys empty:", [[c.value for c in r] for r in out["Keys"].iter_rows(min_row=1, max_row=2, max_col=2)])
