import sys
from openpyxl import load_workbook
path = sys.argv[1]
wb = load_workbook(path)
print("Sheets:", wb.sheetnames)
for ws in wb.worksheets:
    print("=== SHEET", repr(ws.title), ws.dimensions, "state=", ws.sheet_state)
    for row in ws.iter_rows():
        vals = [(c.coordinate, c.value) for c in row if c.value is not None]
        if vals:
            print(vals)
    if ws.tables:
        for name, t in ws.tables.items():
            print("TABLE", name, t)
    if ws.data_validations.dataValidation:
        for dv in ws.data_validations.dataValidation:
            print("DV", dv.sqref, dv.type, dv.formula1)
print("Defined names:", list(wb.defined_names.keys()) if hasattr(wb.defined_names,'keys') else wb.defined_names)
