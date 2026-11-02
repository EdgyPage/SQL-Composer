import sys
import openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
for ws in wb.worksheets:
    print("=== SHEET:", ws.title, ws.dimensions, "state=", ws.sheet_state)
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                print(f"{c.coordinate}: {c.value!r}")
print("TABLES:")
for ws in wb.worksheets:
    for name, ref in ws.tables.items():
        print(ws.title, name, ref)
print("DEFINED NAMES:", list(wb.defined_names.keys()) if hasattr(wb.defined_names,'keys') else wb.defined_names)
