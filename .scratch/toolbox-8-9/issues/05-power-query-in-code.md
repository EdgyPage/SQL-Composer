# Power Query and totals into Hive, in code

Type: task
Status: open
Blocked by: 03, 04
Size: XL

## Question

The code path's second half for M and totals: file 12's rules, written by the Toolbox.

## Done when

- **M read** as file 12's Terms say: a `let` of named steps, each reading the one before, `in`
  naming the one it gives; another query's name a CTE (Q1). Only what file 12's rules list is
  read; any other step is refused, its columns NULL or the query left out, named with why.
- **Each rule of file 12 by its ID**, Q1 to Q7, G1 to G5, T1 to T4, S1 to S3, M1, M2, X1.
- **Total Rows** each a final of their own (T2), reading the Table's final as a CTE.
- Tests: one per rule ID; file 12's Worked patterns each as a test; the three
  `tests/fixtures/workbook_text/` workbooks' saved queries converted.
