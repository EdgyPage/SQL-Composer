import sys
import openpyxl
path = sys.argv[1]
wb = openpyxl.load_workbook(path)
for ws in wb.worksheets:
    print("=== SHEET:", ws.title, "state", ws.sheet_state, "tables:", dict(ws.tables.items()))
    print("   merged:", ws.merged_cells.ranges, "charts:", len(ws._charts), "images:", len(ws._images))
    print("   data validations:", len(ws.data_validations.dataValidation), "cond fmt:", len(ws.conditional_formatting))
    for name, ref in ws.tables.items():
        t = ws.tables[name]
        print("   table", name, ref, [c.name for c in t.tableColumns] if hasattr(t, 'tableColumns') else '')
