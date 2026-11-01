# The scenarios and their answer keys

Type: task
Status: open
Blocked by: 02
Size: L

## Question

The loop needs jobs a zero-context user is given, each with the end its answer key holds,
written before any run (map, "The loop": Q7, Q12).

## Done when

- Nine scenarios, each a folder in `tools/usability_scenarios/`: the job in a user's words, the
  starting tables and files, and an answer key (the tables, their rows, the files the end goal
  holds), split as the map's table says:
  - dev: convert one script with CTEs; new table from its Template; new table from a query;
    references; change a Saved table; E1 one sheet of raw data with formulas; E2 two data
    sources on two sheets, joined; E3 a Power Query step and a Total Row;
  - held out: convert a long script with staging, then promote; upgrade a Project left by 8.0;
    E4 several final Tables across sheets, with Parameters and Keys.
- Each Excel scenario has a presentation workbook, the user's own view, built with `openpyxl`
  on dev as `tools/formula_workbook_examples.py` builds the examples, and an answer key computed
  from its own values, never from the Toolbox's Hive.
- Each answer key is checked by a test on dev: the reference end, reached by hand with the
  Toolbox, passes it, so a key can't ask for what the Toolbox can't do.
- Written and committed before any round runs.
