import sys
import openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
for ws in wb.worksheets:
    for name, ref in ws.tables.items():
        print(ws.title, name, ref)
print([ws.title for ws in wb.worksheets])
print("defined names", list(wb.defined_names.keys()) if hasattr(wb.defined_names,'keys') else wb.defined_names)
