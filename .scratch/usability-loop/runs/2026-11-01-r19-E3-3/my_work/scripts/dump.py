import sys
import openpyxl

path = sys.argv[1]
only = sys.argv[2:] or None
wb = openpyxl.load_workbook(path)
for ws in wb.worksheets:
    if only and ws.title not in only:
        continue
    print(f"=== SHEET {ws.title!r} dims={ws.dimensions} state={ws.sheet_state}")
    for tbl_name, ref in ws.tables.items():
        print(f"   TABLE {tbl_name} ref={ref}")
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                print(f"   {c.coordinate}: {c.value!r}")
print("DEFINED NAMES:", list(wb.defined_names.keys()))
