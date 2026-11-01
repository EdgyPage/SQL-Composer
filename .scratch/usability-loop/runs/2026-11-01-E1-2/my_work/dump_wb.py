import sys
import openpyxl
path = sys.argv[1]
wb = openpyxl.load_workbook(path, data_only=False)
for ws in wb.worksheets:
    print("=== SHEET:", ws.title, ws.dimensions)
    for row in ws.iter_rows():
        vals = [(c.coordinate, c.value) for c in row if c.value is not None]
        if vals:
            print(vals)
