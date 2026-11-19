# Copilot file 20: PivotTables into Hive

Type: task
Status: open
Blocked by: 06, 10
Size: L

## Question

The Copilot path's pivot rules, with the same IDs as ticket 06's (round 2, Q5: "make pivot
instructions too").

## Done when

- **`tools/copilot_sources/20_*.txt`**, written to `copilot/` by `tools/copilot_files.py`, at
  most 9,000 characters, in files 11 and 12's shape: Patterns, Terms, Rules by ID, Worked
  patterns, Self-check.
- It holds every rule in the map's Notes "PivotTables into Hive" and "Pivot filters", and has
  Copilot write `-- Pivot filter: <kind> <field>` above each such condition.
- **File 15** gives a pivot its role (a step when GETPIVOTDATA reads it, else a final), and
  **file 11's X1** no longer names PivotTables as left alone; each stays within 9,000.
- **`00_start_here.txt`** loads 20 with 15, 11 and 12 for a workbook with a pivot.
- The all-in-one file is merged again.
