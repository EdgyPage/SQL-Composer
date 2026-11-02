import sys
from openpyxl import load_workbook
path = sys.argv[1]
wb = load_workbook(path)
for ws in wb.worksheets:
    print("=== SHEET:", ws.title, ws.dimensions, "state:", ws.sheet_state)
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                print(c.coordinate, repr(c.value))
