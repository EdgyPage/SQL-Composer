# The usability round

Type: task
Status: resolved
Blocked by: 01, 14, 16
Size: M

## Question

Can a user with no context still follow the Workflows from what main ships (Q22)?

## Done when

- `plan` runs on every scenario, and only those it says to run are given to agents (ticket
  01's memo).
- **W8 is redone** to start its Scheduled run through the schedule Workflow.
- **A new W9** converts a script with a Script tag, answers it with `hivevar(...)` and a default,
  then exports it for a scheduler, and checks the `.hivevars` file against its answer key.
- Every dev scenario the round runs passes three of three, held-out once, recorded in
  `.scratch/usability-loop/results.md` with each run's inputs.
- **The beginner reader** reads the Workflows overview page and a lineage page's side panel,
  and its report is linked here.
- Each finding is fixed in what a user reads, or recorded for the next version.

## Answer

Run 2026-11-13 on dev at 6e751fe5 (8.7). Yes: a user with no context follows every Workflow
and the Excel path from what main ships. The round's record is `.scratch/usability-loop/
results.md`'s "The 8.7 round", with each run's row and folder.

### W8 and W9 (6e751fe5)

- **W8** now starts its Scheduled run through the schedule Workflow: its message says "starting
  it through the Workflow that makes a Scheduled run"; its key holds
  `admin/workflows/schedule/schedule.ipynb` naming `team_week`; its reads add "The Workflows"
  and `follow_a_workflow`; `reference_w8` types `NAME` into the Workflow's names cell and runs
  it (`finish("schedule", ...)`) in place of calling `project.new_scheduled_run`.
- **W9**, new, dev: `from_your_team/period_runs.hql` writes `mart.period_runs` with a bare
  `<PARM="PERIOD_END"/>` (it ran with 2026-09-24). Its user copies it to
  `mart_dev.period_runs`, leaves PERIOD_END for the scheduler with 2026-09-24 as its value
  when none is given, and writes out the Hive with its values file. Its key: the table's rows
  (from the original Hive as it ran), `compare.md` Passed, the `.hql` holding
  `'${hivevar:PERIOD_END}'` and the `.hivevars` holding `--hivevar PERIOD_END=2026-09-24`.
  `reference_w9` converts, answers `hivevar("PERIOD_END", default="'2026-09-24'")` in the
  decisions cell, finishes and runs `export_hive()` in the Table notebook's folder;
  `tests/journeys/test_usability_scenarios.py` holds its end, and W8's, to their keys.

### The round

- `plan` on all 15 scenarios said "run it" for each (no run recorded with these inputs, since
  ticket 01's per-part hash), so none was memoized and no memoized run is named.
- 41 runs, fresh `zero-context-user` agents on Haiku, each run's inputs in its
  `_loop/inputs.json` and its row's hash: every one passed.
  - Dev, 3/3 each: W1 (actions 4, 4, 8), W2 (2, 6, 11), W3 (7, 7, 10), W4 (4, 11, 4), W5 (10,
    9, 8), W6 (6, 11, 13), W7 (7, 12, 5), W8 (10, 4, 6), W9 (6, 10, 11), E1 (7, 8, 9), E2 (8,
    10, 19), E3 (8, 10, 8). The Workflow runs asked nothing; each Excel converter asked Copilot
    once, routed through two `copilot-proxy` agents on Haiku as `docs/usability-loop.md` says.
  - Held-out, once each: H1 (5), H2 (3), E4 (20, one question).
- The agents' Python had lost its packages' `__init__.py` files; it was made again first.

### Findings and what was done

Fixed (b499f940, 7ff6b66d):
- README, Scheduled runs step 5: a parameter's days are worked out in `statements()` and passed
  plain, since a logic function that works on a day's text refuses a `run_value(...)` (W8, all
  three hit it); a write named in `statements()` takes the build's place (W8-1, W8-3, and
  8.6's round). Copilot file 18 says the first too.
- README, convert step 5: `compare.md` counts the other Partitions, listed with
  `query("SHOW PARTITIONS ...")` (W1-1, W1-3, H1); its Decision rules: a script's `NOT IN`
  names an unproposed Key's column (W7-3); section 2, step 4: refresh the Reference sheet after
  a hand change (W4-1).
- The loop's stand-in warehouse no longer lets sqlglot warn on `SET hivevar:` (W9, all three
  read it as a failure; a team's warehouse prints nothing), test first in
  `tests/test_usability_loop.py`. No Toolbox bug was found.
- `docs/usability-loop.md`, step 3.5: the words to resume an agent that handed back at a
  QUESTION (three Excel converters only repeated their report until told their run was not
  over).
- Beginner reader (report:
  [beginner-reader-ticket-15.md](../reports/beginner-reader-ticket-15.md)), on the Workflows
  overview: 1.1, the names cell is the code cell under the setup cell, `connect(...)` in the
  setup cell, on the page and in the README's "The Workflows" step 1 (drift D522); 1.5, after
  mending step 2 run "Run up to your Decisions" again; 1.8, DEV is filled in in
  `admin/databases.py`; 1.12, how a scheduler's value reaches a Statement.

Recorded for the next version (results.md's "The 8.7 round" lists the run findings):
- The `scheduled_run` Template's `# scheduled` comment, its `leave_out` example and its
  "Fill in every `<...>`" text (W8), since a Template's text changes with a version's Upgrade;
  `DATE_ADD(x, 1 * -1)` for `date_sub` (W7, W9); `conversion/*.hql` showing raw `<PARM>` tags
  unexplained (W6-3); the Templates' unmarked connect line after an Upgrade (H2).
- Beginner reader, Workflows overview: 1.2 (no way back to "Every Workflow" after a click),
  1.3 (the "Step by step" cells unmentioned), 1.4 (the `your decision` tag on writing logic),
  1.6 (DESCRIBE, Reference sheet, Database module, Run value and seed missing from the Words
  list), 1.7 (convert's eight names unexplained), 1.9 ("Check first"), 1.10
  (`location_root`), 1.11 (upgrade drawn last), 1.13 (Copilot files by number, a plain-text
  README name, "From excel").
- Beginner reader, lineage panels: 2.1 (Copy leaves out the Session settings' SET lines), 2.2
  (the Scheduled run's page names each Statement after its table, so lines repeat it and the
  Keys lines look contradictory), 2.3 (a column box's panel doesn't name the box), 2.4 (a
  calculated column shown twice), 2.5 ("Run values: none" unsaid), 2.6 (a Run value line reads
  like a module path), 2.7 (fixed days in a weekly run's upstream writes), 2.8 ("comes back to
  you"), 2.9 (legend and label wording), 2.10 (no Project lineage page in the Example project
  to show "Written by Scheduled runs").
