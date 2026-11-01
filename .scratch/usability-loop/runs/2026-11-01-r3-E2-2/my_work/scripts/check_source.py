import sys
import openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
for ws in wb.worksheets:
    print("SHEET", ws.title, "merged:", ws.merged_cells.ranges, "dv:", len(ws.data_validations.dataValidation), "cf:", len(ws.conditional_formatting))
    hidden_rows = [r for r, d in ws.row_dimensions.items() if d.hidden]
    hidden_cols = [c for c, d in ws.column_dimensions.items() if d.hidden]
    print("  hidden rows", hidden_rows, "hidden cols", hidden_cols)
    for row in ws.iter_rows():
        for c in row:
            if c.comment:
                print("  comment", c.coordinate, c.comment.text)
            if c.value is not None and c.data_type not in ("s", "f", "n"):
                print("  odd type", c.coordinate, c.data_type, repr(c.value))
            if isinstance(c.value, str) and c.value.startswith("=") and c.data_type == "f":
                pass
    types = {}
    for row in ws.iter_rows(min_row=2):
        for c in row:
            if c.value is not None:
                types.setdefault(c.column_letter, set()).add(type(c.value).__name__)
    print("  value types by column", {k: sorted(v) for k, v in types.items()})
