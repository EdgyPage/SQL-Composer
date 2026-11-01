import sys
import openpyxl
path = sys.argv[1]
wb = openpyxl.load_workbook(path)  # formulas kept
print("SHEETS:", wb.sheetnames)
for ws in wb.worksheets:
    print("=" * 80)
    print("SHEET:", ws.title, "dims:", ws.dimensions, "max_row", ws.max_row, "max_col", ws.max_column)
    print("tables:", {n: t for n, t in ws.tables.items()})
    print("merged:", ws.merged_cells.ranges)
    for row in ws.iter_rows():
        vals = [(c.coordinate, c.value) for c in row if c.value is not None]
        if vals:
            print(vals)
print("DEFINED NAMES:", list(wb.defined_names.keys()) if hasattr(wb.defined_names, 'keys') else wb.defined_names)
