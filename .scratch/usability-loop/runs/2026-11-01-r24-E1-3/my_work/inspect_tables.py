import sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1])
for ws in wb.worksheets:
    print(ws.title, "tables:", [(n, ref) for n, ref in ws.tables.items()], "dv:", len(ws.data_validations.dataValidation))
    for t in ws.tables.values():
        print("  table", t.name, t.ref, t.tableStyleInfo.name if t.tableStyleInfo else None, t.totalsRowCount)
