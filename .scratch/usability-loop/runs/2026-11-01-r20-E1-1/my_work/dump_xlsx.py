import sys
import openpyxl

path = sys.argv[1]
wb = openpyxl.load_workbook(path)
for ws in wb.worksheets:
    print(f"=== SHEET: {ws.title!r} dims={ws.dimensions} max_row={ws.max_row} max_col={ws.max_column}")
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                print(f"  {c.coordinate}: {c.value!r}")
    if ws.tables:
        for name in ws.tables:
            t = ws.tables[name]
            print(f"  TABLE {name} ref={t.ref}")
print("defined names:", list(wb.defined_names.keys()) if hasattr(wb.defined_names, 'keys') else wb.defined_names)
