import sys
import openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if c.data_type == "f":
                print(ws.title, c.coordinate, c.value)
    print("tables", {n: ws.tables[n].ref for n in ws.tables})
