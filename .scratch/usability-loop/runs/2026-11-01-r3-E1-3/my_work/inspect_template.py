import sys
import openpyxl
path = sys.argv[1]
wb = openpyxl.load_workbook(path)
for ws in wb.worksheets:
    print("=== SHEET:", ws.title, ws.dimensions, "state:", ws.sheet_state)
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                print(f"{c.coordinate}: {c.value!r}")
    for name in ws.tables:
        t = ws.tables[name]
        print("TABLE", name, t.ref, "totalsRow:", t.totalsRowCount, "headerRow:", t.headerRowCount)
