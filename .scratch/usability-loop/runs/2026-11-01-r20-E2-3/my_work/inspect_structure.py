import sys, zipfile
from openpyxl import load_workbook
for path in sys.argv[1:]:
    print("=====", path)
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            print("  zip:", n)
    wb = load_workbook(path)
    print("defined names:", list(wb.defined_names.keys()) if hasattr(wb.defined_names,'keys') else wb.defined_names)
    for ws in wb.worksheets:
        print("sheet", ws.title, "tables:", dict(ws.tables.items()), "merged:", ws.merged_cells.ranges, "hidden rows:", [r for r,d in ws.row_dimensions.items() if d.hidden], "hidden cols:", [c for c,d in ws.column_dimensions.items() if d.hidden], "charts:", len(ws._charts))
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None and c.data_type == 'f':
                    pass
