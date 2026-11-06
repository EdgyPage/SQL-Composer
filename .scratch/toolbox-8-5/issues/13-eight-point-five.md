# 8.5: the Upgrade step and the raise

Type: task
Status: resolved
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
Built 2026-11-05.

- `upgrades.to_8_5`, `"8.5"` in STEPS:
  - **admin/databases.py** is written as 8.5's `project.start()` writes it
    (`project.DATABASES_TEXT`), each name 8.4 gave kept, each `"location_root"` left `<...>`
    and marked: `fill in "location_root", the folder DEV's tables' files go under ...`, naming
    the folder a Table reference's location shows under `/<database>.db/` today, when one
    does (`_databases_as_settings`, `_root_to_fill`). The file as it was is kept.
  - **PARTITION into PARTITIONS**: the value 8.4's convert names cell gave is read before the
    notebooks are written again, and written into PARTITIONS as a list of it
    (`_partition_given`, `_partitions_given`); step 7's cell is 8.5's, `partitions=PARTITIONS`.
  - **The Workflow notebooks** are written again top to bottom (ticket 02), each name and step
    cell you wrote in kept, as 8.4's step does.
  - **Marked**: an all_tables `"location_root"` a kept decisions cell gives
    (`_mark_all_tables_location_root`); the first import of dev's Building block in each prod
    copy's notebook, promoted before 8.5 (`_mark_prod_copies_importing_dev_blocks`).
- `version.txt` says 8.5; `__init__`'s doctest too.
- `tests/upgrade_from/8.4/`: the Example projects as 8.4 shipped them (97ea0bdf), without their
  Lineage pages. The chain test runs 8.3 and 8.4 to 8.5; its comparison leaves out each
  UPGRADE mark's line (what a mark asks is the user's), the 8.5 Example projects' by-hand
  changes (`GAINED_BY_HAND`: the intermediate's saved script, its README, its proposed Key
  accepted) and a batch finished before 8.5 (`LEFT_AS_IT_WAS`: its record and its scripts'
  copy are history).
- Tests: `tests/test_upgrades.py`'s 8.5 tests (the settings written and marked; PARTITION
  carried; an all_tables location_root marked; a prod copy importing dev's block marked); the
  7.1 test counts the 8.4 and 8.5 steps.
- Ticket 12's round runs after this one, on 8.5 as it ships, since the version is in what a
  user reads.
