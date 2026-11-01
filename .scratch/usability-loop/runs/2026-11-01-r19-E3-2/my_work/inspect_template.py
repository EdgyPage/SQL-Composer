import sys
import openpyxl

path = sys.argv[1]
wb = openpyxl.load_workbook(path)
print("sheets:", wb.sheetnames)
print("defined names:", list(wb.defined_names.keys()) if hasattr(wb.defined_names, "keys") else wb.defined_names)
for ws in wb.worksheets:
    print("=" * 70)
    print("SHEET:", ws.title, "dims:", ws.dimensions, "max_row", ws.max_row, "max_col", ws.max_column)
    print("tables:", {name: t for name, t in ws.tables.items()})
    for row in ws.iter_rows():
        vals = [(c.coordinate, c.value) for c in row if c.value is not None]
        if vals:
            print(vals)
