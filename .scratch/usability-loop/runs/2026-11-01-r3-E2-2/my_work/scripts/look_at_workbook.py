import sys
import openpyxl
from openpyxl.utils import get_column_letter
path = sys.argv[1]
wb = openpyxl.load_workbook(path)
print("Sheets:", wb.sheetnames)
for ws in wb.worksheets:
    print("=== SHEET", ws.title, ws.dimensions, "state", ws.sheet_state)
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                print(f"  {c.coordinate}: {c.value!r}")
    print("  tables:", {n: ws.tables[n].ref for n in ws.tables})
print("Defined names:", {n: wb.defined_names[n].attr_text for n in wb.defined_names} if hasattr(wb.defined_names,'keys') else wb.defined_names)
