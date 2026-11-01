# The scenarios and their answer keys

Type: task
Status: resolved
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
- E3's Power Query: openpyxl can't author one, so its M code is written for the scenario and
  put in the workbook itself, where whoever opens the file reads it (the user, 2026-11-01:
  "Generate the code of power query and throw it in conversion process. Assume the model can
  access it from the file."). It goes in as the Formula workbook's Steps sheet tells a user to
  record a query, or, where it says nothing, on a sheet of its own named for the query. The
  relay's workbook text (`usability_loop.workbook_text`) shows it to Copilot with the rest.
- Each answer key is checked by a test on dev: the reference end, reached by hand with the
  Toolbox, passes it, so a key can't ask for what the Toolbox can't do.
- Written and committed before any round runs.

## Answer

Built 2026-11-01.

- `tools/usability_scenario_files.py` builds the scenarios into `tools/usability_scenarios/`,
  eleven, not the "nine" this ticket first counted: the list above holds eight dev (W1 to W5,
  E1 to E3) and three held out (H1, H2, E4). Each folder holds `scenario.json`, its given files,
  the Hive its team's warehouse ran, any presentation workbook, and `key.json`. W5 holds no
  Project of its own: its `start_from: "W2"` has `prepare` build W2's reference end and start
  W5 from it.
- Keys come from outside the Toolbox's own work: a Workflow scenario's from the warehouse, the
  rows its original Hive wrote (W1, H1) or an independent query's (W2, W3, W5), on the Example
  database; W4's and H2's from the files the end must hold; an Excel scenario's computed in
  Python from its workbook's raw rows, as its formulas compute them.
- `reference_end` reaches each end with the Toolbox, through each Workflow notebook's names and
  decisions cells and `project.run_workflow`, from the notebook's own folder as its last cell
  runs; an Excel one with the Hive its formulas map to, made into tables by new_table, each
  table's Key answered (E4's two Tables, the Rate Parameter and the value typed over a formula
  among them). `tests/journeys/test_usability_scenarios.py` holds each end to its key, an Excel
  end to leave no type guessed, a run that reached none failing it, the splits and phases, and
  the committed folders to a fresh build.
- `usability_loop.prepare` copies in a Project a scenario starts from (W5, built from W2's end;
  H2, the 8.0 freeze), its warehouse.py given the team's connection, and creates and writes its
  Saved tables when the scenario says so.
- E3's Power Query: its M code written for the scenario and kept on a sheet of the workbook
  ("Power Query CleanRuns"), as the user said. Whether it reaches the converter, through the
  filled-in copy the non-technical user makes, is what the Steps sheet tells them: round one
  measures it. E3's Total Row isn't in its key: the Toolbox refuses a subtotal row in a Saved
  table ("Write the plain GROUP_BY into the Saved table, and add the subtotals in the Statement
  that reads it"), so a Total Row is added by a read. Copilot file 12 maps a Total Row to WITH
  ROLLUP without saying so: a likely gap for round one.
- Building the references found two Toolbox gaps, each fixed in a ticket of its own: 08, a
  calculation's type, and 09, the Example database's subtotals and a group's column beside an
  aggregate.
- Code review. Standards: the grouping-set and two-step rewrites share one output-renaming and
  one in-place helper, with names for what each holds, deterministic subquery names and the
  innermost SELECT worked first; the builder's references run through `finish`, its locations
  through `where_each_goes`, its upgrade marks through `without_upgrade_marks`, and E4's Hive
  from `TYPED_OVER` and `CENTS_A_MINUTE`; `keys` given for every Excel end, so no `or {}`. Left:
  `Scenario.project` and `start_from` as two optional strings, since a scenario names at most
  one and `scenario.json` reads plainest so; the lazy import of the builder in
  `bring_in_the_project`, which it names; a new scenario touching its builder, its reference
  and its key, as each says a different thing. Spec: the miscount above; E4's Keys now answered
  and checked; no type left guessed now tested; the E3 Total Row and the Power Query reaching
  the converter, above; the loop's `project` and `start_from` serve W5 and H2, which this
  ticket lists.
