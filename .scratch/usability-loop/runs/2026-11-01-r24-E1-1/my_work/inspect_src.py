import sys
import openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
for ws in wb.worksheets:
    print("SHEET", ws.title, "merged:", ws.merged_cells.ranges, "tables:", list(ws.tables.keys()))
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                print(" ", c.coordinate, type(c.value).__name__, repr(c.value), c.number_format if c.data_type == 'n' else '')
