import sys
from openpyxl import load_workbook
for path in sys.argv[1:]:
    print("=====", path)
    wb = load_workbook(path)
    for ws in wb.worksheets:
        print("--- sheet:", ws.title, ws.dimensions, ws.sheet_state)
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None:
                    print(c.coordinate, repr(c.value))
