import sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1])
for ws in wb.worksheets:
    print("==", ws.title, ws.dimensions, dict(ws.tables.items()))
