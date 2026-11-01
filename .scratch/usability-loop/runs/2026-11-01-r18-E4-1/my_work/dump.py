import sys
import openpyxl
path = sys.argv[1]
wb = openpyxl.load_workbook(path)
print("SHEETS:", wb.sheetnames)
print("DEFINED NAMES:", list(wb.defined_names.keys()) if hasattr(wb.defined_names,'keys') else wb.defined_names)
for ws in wb.worksheets:
    print("=== SHEET", ws.title, ws.dimensions, "state", ws.sheet_state)
    for row in ws.iter_rows():
        vals = [(c.coordinate, c.value) for c in row if c.value is not None]
        if vals:
            print(vals)
    print("tables:", {n: ws.tables[n].ref for n in ws.tables})
