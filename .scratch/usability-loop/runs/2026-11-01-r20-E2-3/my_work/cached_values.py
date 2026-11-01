import sys
from openpyxl import load_workbook
wb = load_workbook(sys.argv[1], data_only=True)
for name in ["Teams"]:
    ws = wb[name]
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
        print(row)
ws = wb["Runs"]
for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
    print(row)
