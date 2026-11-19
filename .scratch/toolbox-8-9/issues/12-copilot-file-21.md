# Copilot file 21: growing a converted pivot

Type: task
Status: open
Blocked by: 08, 11
Size: M

## Question

What Copilot adds to a pivot after it is converted, and how a Pivot filter scales (round 1, Q8;
round 3, Q4; the user's "copilot hint that the filter or sliced views could be aggregated in to
batched inserts on a table or different tables").

## Done when

- **`tools/copilot_sources/21_*.txt`**, at most 9,000 characters, loaded with 03, 05 and 06,
  writes Toolbox code in the converted Table notebook, never a change to the workbook:
  - add-ons: % of a total, running totals, ranks, a calculated field, date grouping, the wide
    shape of a Column field, totals as a rollup Statement;
  - Pivot filters at scale: each proposal of ticket 08's Decision, when to pick it, and each
    layer's table count, with "a filter with 100 conditions would make 100 tables, but the
    higher layer filter may have only 3, which is manageable";
  - what no Decision does: two pivots differing only in their filter made one table, written
    as batched inserts.
- **`00_start_here.txt`** says when to load it.
- **Its tasks** in `tools/copilot_eval_tasks.py`, dev and held-out, scored as the other files'
  are.
