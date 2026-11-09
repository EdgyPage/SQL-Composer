# 8.6: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 10
Size: M

## Question

The user named 8.6 (map, "The version").

## Done when

- `to_8_6` in `upgrades.py`'s STEPS: warehouse.py gains `connect`, `query` and `execute` as
  8.6 writes them, the user's `conn = ...` line and what it imports kept and marked to move
  into a `connect(...)` call; each Toolbox notebook's setup cell gains its `connect(...)` line;
  `scheduled_runs/`, the Template and `admin/scheduled_runs.ipynb` made.
- `tests/upgrade_from/8.5/` frozen from the Example projects as 8.5 left them, without their
  Lineage pages; the chain test runs 8.3 to 8.6.
- `version.txt` says 8.6.

## Answer
