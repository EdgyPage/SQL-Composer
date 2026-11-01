import sys
from openpyxl import load_workbook
p = sys.argv[1]
wb = load_workbook(p)
for ws in wb.worksheets:
    print("=== SHEET", ws.title, ws.dimensions, ws.sheet_state)
    for row in ws.iter_rows():
        vals = [(c.coordinate, c.value) for c in row if c.value is not None]
        if vals:
            print(vals)
    if ws.tables:
        for name, t in ws.tables.items():
            print("TABLE", name, getattr(t, "ref", t))
print("DEFINED NAMES", list(wb.defined_names.keys()) if hasattr(wb.defined_names,'keys') else wb.defined_names)
