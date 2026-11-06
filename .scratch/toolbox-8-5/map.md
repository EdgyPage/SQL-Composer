# Toolbox 8.5: fewer of your actions in the Workflows, and Database settings

Label: wayfinder:map

The user (2026-11-05), with 8.4 exported to main: "now that the conversion work is done, let's
take a look at automating and speeding up the workflows. I want to take a look at if there are
opportunities to reduce the amount of manual code editting and cell additions." Grilled the same
day, every question settled. Speed means **fewer of the user's actions** (Q1: "a only. less
steps while maintaining functionality is good"), not wall-clock time. The user named the
version 8.5.

## Notes

### What the user does by hand today (8.4 at 97ea0bdf)

An inventory of every Workflow, from `workflows.py`, the journeys, the README template and the
usability loop's runs (206 run folders):

- **No step is FIDDLING**, but hand work hides in decision and file steps, and the journeys do
  some for the user unlisted: set `conn`, fill DEV and PROD, save the .hql beside the notebook,
  write `building_blocks/run_values.py`, type the whole decisions cell.
- **Up and down the notebook.** The convert notebook's decisions cell is cell 4, at the top;
  `project.check()`, which prints the DECISIONS to paste there, is cell 8, under step 2; step 3,
  which writes it in, is cell 10. The user: "I want sequential steps without having to roll back
  up and down."
- **Most often hit, every run**: the DECISIONS paste-and-fill; typing the names cell; saving the
  scripts into `admin/workflows/convert/`.
- **Often hit**: writing `run_values.py` and `project.register` from no cell (all three W7
  runs); a Key chosen by typing `check_key` lines (about 7 runs); a Table reference's TODO lines
  (about 8); comparing another Partition after the batch finished, from a script (about 8).
- **Real judgement, kept**: `conn`; DEV and PROD; a new table's logic; change_a_saved_table's
  Admin statement; the Excel path's workbook.
- The 40 run folders holding scripts that edit notebooks overstate it: the loop's agents have no
  Jupyter. Which cells they edited (names, decisions) is the signal.

### Notebooks read top to bottom (Q2, Q7, Q10)

The notebook stays the surface. Convert, promote, new_table and references each open with the
intended path, in order, never rolling back up:

1. the names cell;
2. **"Run up to your Decisions"**: `project.run_workflow(...)`, stopping at the first Decision
   and printing the DECISIONS to paste;
3. the decisions cell, directly below it;
4. **"Run the rest"**: `project.run_workflow(...)` again, from where it stopped.

Below, **"Step by step"**: each step's own cell, as today, each decision step with its
`project.check()` cell (8.4's ticket 14), for running or running again one step on purpose. A
wrong answer is mended in cell 3 and cell 4 run again: still downward. Copying and pasting
stays (Q7, "I'm ok with copying and pasting"): what changes is that the cells it goes between
sit together. change_a_saved_table and upgrade stay step by step: they are short.

### The names cell (Q8, Q9, Q6e)

- **FILES** defaults to every `.hql` beside the convert notebook, and takes a path anywhere, so
  scripts needn't be copied in. **NAME** stays typed: a batch's name is how it is found later.
- **promote's TABLES** defaults to every finished, unpromoted table.
- **PARTITIONS**, a list, in place of 8.4's PARTITION: the compare step compares each, the latest
  when it is left empty, as today. No script of one's own to compare a backfill.
- **One batch per script**, a switch: `FILES = ["a.hql", "b.hql"]` makes a batch of each, named
  for its file, one decisions cell for all (DECISIONS is keyed by table; `"all_tables"` spans
  them). For simple, unrelated scripts, the user's words: "I do one at a time now because it's
  hard to think about more than one at the moment. I am open to designing batch designs and
  lists for simple, unrelated conversions." Batches whose tables read each other's are refused,
  naming the pair.

### Fewer Decisions written out (Q4, Q5, Q14, Q15)

- **A Run value on demand** (Q4): `project.new_run_value("period_end",
  latest_partition="ops.job_runs.dt")` writes the function into `building_blocks/run_values.py`
  with its imports, and registers it, ready to import in the decisions cell. No file is shipped
  in every Project (8.4's ticket 14: no dead code). The common case, the latest Partition of a
  table, is the one it writes; anything else is the file to edit.
- **A batch's proposals accepted at once** (Q5): a proposed Key, which the Guards then prove or
  refuse, is accepted for the whole batch in one answer. A guessed column type is not: it stays
  each table's. (A location, once Database settings place it, is no Decision at all.)
- **Proposed TODO lines** (Q14): a Table reference's "what one row is" is proposed from its Key
  ("One row per run_id."), left open with none; its `does_not_add_up` from its columns' names
  and types (`avg_*`, `*_ratio`, `*_pct`, `*_rate`, a double `*_per_*`). Each is written
  `# proposed`, as a proposed Key is.
- **The Key step checks its proposal** (Q15): the references Workflow's Key step runs
  `check_key` on the proposed Key itself, through the user's query, and prints the verdict and
  the line to accept it.

### Database settings (Q6, Q6a, Q6c, Q11, Q12, Q13)

`admin/databases.py`'s DEV and PROD become two dicts, under the same names in both, checked
each time they are read:

```python
DEV = {"database": "mart_dev", "location_root": "/data/team/dev", "run_as": "svc_team_dev"}
PROD = {"database": "mart", "location_root": "/data/team/prod", "run_as": "svc_team_prod"}
```

- `"database"` is needed; `"location_root"` is the Toolbox's; any other is the user's own. A
  name in one and not the other is refused, naming it, so dev to prod is a lookup by name.
- **Two roots** (Q6c, "no, there are two roots, dev and prod"): DEV's places dev tables, PROD's
  prod copies, each `<root>/<database>.db/<table>`. It takes the place of `"all_tables"`'s
  `location_root` and of promote renaming a dev location's `.db` folder. A table's own
  location still wins.
- **The user's own values reach their code** through `database_settings(name)`, the settings of
  the Database a table is in. The Toolbox carries them and never acts on them.
- **Connections stay the user's** (Q11: "I can handle this on my own end editting as needed.
  ... What's implemented currently is sufficient."). Different accounts make different
  connections at work, credentials given at run time, the user name known: that stays in the
  user's code. One `conn` in warehouse.py, as today; no connection per Database.

### Building blocks in prod (Q6d)

"I may want to keep them separate because dev is lower stakes." Promote copies each Building
block a promoted table imports, Run values among them, into `building_blocks/prod/`, as it
copies a table: the prod table imports the prod copy; promoting again archives the old copy
into admin/removed/ first; `project.check()` names a prod copy edited by hand. Dev's blocks
change freely, prod's only when promoted. A block that names the Dev Database is still refused.

### What promote does, as it stands (checked against the code)

A copy, not a move: a prod copy of each table's notebook and Table reference, dev staying the
source. A source in another Database (`ops.job_runs`) is read as it is by both copies; a source
that is a dev table is promoted with it, or promote refuses. So a prod table never reads a
dev-only one.

### The version

8.5, named by the user. It changes `admin/databases.py`'s shape, the Workflow notebooks and the
Building blocks' folder: its Upgrade step (13) turns the two strings into `{"database": ...}`,
marks `"location_root"` in each to fill in, writes the Workflow notebooks again in the new
order (keeping each name and answer given), and freezes the Example projects at 8.4 in
`tests/upgrade_from/8.4/`.

### Words

- **Database settings** (CONTEXT.md, 2026-11-05): what differs between the Dev and Prod
  Databases, one set for each under the same names. _Avoid_: config, environment, profile.
- **Promotion** widened: a prod copy of each table's code and of each Building block it uses.
- Not new words: "Run up to your Decisions" and "Run the rest" are cells' headings; "Step by
  step" a section's.

## Tickets

- [01 A journey of the 8.5 path, counting your actions](issues/01-a-journey-counting-actions.md)
- [02 Notebooks read top to bottom](issues/02-notebooks-top-to-bottom.md)
- [03 FILES and promote's TABLES default](issues/03-names-cell-defaults.md)
- [04 PARTITIONS for the compare](issues/04-partitions.md)
- [05 One batch per script](issues/05-one-batch-per-script.md)
- [06 project.new_run_value](issues/06-new-run-value.md)
- [07 A batch's proposed Keys accepted at once](issues/07-accept-proposed-keys.md)
- [08 The references Workflow proposes and checks](issues/08-references-propose-and-check.md)
- [09 Database settings](issues/09-database-settings.md)
- [10 Building blocks in prod](issues/10-prod-building-blocks.md)
- [11 The docs and the Copilot files](issues/11-the-docs.md)
- [12 The usability round](issues/12-the-usability-round.md)
- [13 8.5: the Upgrade step and the raise](issues/13-eight-point-five.md)

One at a time, by number, the user's habit. The real dependencies are in each ticket's
`Blocked by:`.

## Records this changes

- `sqlglot_composer/`: `workflows.py` (02 to 05, 07, 08), `project.py` (03 to 10),
  `decisions.py` (07, 09), `comparisons.py` (04), `project_files.py` and the Templates (06, 08,
  10), `upgrades.py` and `version.txt` (13), `public.py` (09).
- `tests/journeys/test_workflow_journeys.py` (01 onward), `tests/test_no_cell_of_your_own.py`
  and `tests/test_workflow_steps.py` (02), `tests/test_upgrades.py` (13).
- CONTEXT.md: Database settings and Promotion (already, 2026-11-05).
- CLAUDE.md: this map (with the map); 8.5 (13). CHANGES.md's `## 8.5` (02 onward).
- `docs/workflows.md`, the README, the how-tos, the Copilot files (11).
- `tools/usability_scenario_files.py` and `.scratch/usability-loop/results.md` (12).

## Decisions so far

## Not yet specified

## Out of scope

- Wall-clock time of a step (Q1).
- A connection for each Database, or the Toolbox handling credentials (Q11).
- Shortening change_a_saved_table and upgrade, and the Excel path (Q3): mostly real judgement.
- Batches that read each other's tables in one list (Q6e).
- Accepting guessed column types in bulk (Q5).
