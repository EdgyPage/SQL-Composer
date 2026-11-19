# The pivot tasks and their baseline

Type: task
Status: open
Blocked by: 02, 03
Size: L

## Question

The Excel evaluation's pivot tasks, written before file 20 as 7.2 wrote its tasks before file
11 (round 3, Q9).

## Done when

- **About 40 tasks, 20 dev and 20 held-out**, in `tools/excel_eval_tasks.py`, each a workbook
  from ticket 02's tool with a reference Hive per final: each case in the map's Notes alone,
  and a combinations tier mixing pivots with formulas and M (such as a query feeding a pivot
  with a slicer, read back by GETPIVOTDATA).
- **The scorer** scores a pivot's finals and its totals' finals, and counts its Pivot filter
  marks (the `-- Pivot filter:` comment) under `named`.
- **The baseline**: each split answered without file 20, on Haiku and Sonnet, recorded in the
  ledger, in `.eval-local/`.
- `docs/copilot-eval.md`'s Excel section names the new tasks.
