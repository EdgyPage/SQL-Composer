import sys
import openpyxl

path = sys.argv[1]
wb = openpyxl.load_workbook(path)  # formulas as written
print("SHEETS:", wb.sheetnames)
for ws in wb.worksheets:
    print("=" * 70)
    print("SHEET:", ws.title, "dims:", ws.dimensions, "state:", ws.sheet_state)
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                print(f"  {c.coordinate}: {c.value!r}")
    if ws.tables:
        for name, tbl in [(t.name, t) for t in ws.tables.values()]:
            print("  TABLE", name, tbl.ref, "totals:", tbl.totalsRowCount)
print("DEFINED NAMES:", list(wb.defined_names.keys()) if hasattr(wb.defined_names,'keys') else wb.defined_names)
