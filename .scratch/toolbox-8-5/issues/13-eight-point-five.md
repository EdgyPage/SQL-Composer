# 8.5: the Upgrade step and the raise

Type: task
Status: open
Blocked by: 12
Size: M

## Question

The user named 8.5 (map, "The version").

## Done when

- `to_8_5` in `upgrades.py`'s STEPS: DEV and PROD strings become `{"database": ...}`, each with
  `"location_root"` marked to fill in, its mark naming the root an 8.4 location used; each
  Workflow notebook written again in the new order, each name and answer given kept; PARTITION
  carried into PARTITIONS.
- `tests/upgrade_from/8.4/` frozen from the Example projects as 8.4 left them, without their
  Lineage pages; the chain test runs 8.3 and 8.4 to 8.5.
- `version.txt` says 8.5.

## Answer
