import sys, openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
for ws in wb.worksheets:
    print("SHEET", ws.title, "state", ws.sheet_state, "hidden rows", [r for r,d in ws.row_dimensions.items() if d.hidden], "hidden cols", [c for c,d in ws.column_dimensions.items() if d.hidden])
    print("  dv:", len(ws.data_validations.dataValidation), "cf:", len(ws.conditional_formatting), "comments:", [c.coordinate for row in ws.iter_rows() for c in row if c.comment])
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None:
                print("   ", c.coordinate, type(c.value).__name__, repr(c.value)[:70], c.number_format if c.number_format!='General' else '')
print("defined names:", list(wb.defined_names.keys()))
