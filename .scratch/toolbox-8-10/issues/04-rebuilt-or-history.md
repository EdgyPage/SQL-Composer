# Rebuilt or History: each table's kind, a Decision proposed from its write

Type: task
Status: resolved
Blocked by: -
Size: M
Spec: [specs/04-rebuilt-or-history.md](../specs/04-rebuilt-or-history.md)

## Question

Nothing asks whether a table is rebuilt whole by each write or keeps its past rows (round 1,
Q7 and Q9; round 2, Q6; CONTEXT.md's Rebuilt table and History table). The kind decides whether
a table has a Seed (ticket 05).

## Done when

- **Each table convert and `new_table` write has a kind**, Rebuilt or History, in its Table
  reference, answered in the Workflow's decisions cell as 8.5's Decisions are, never by a hand
  edit; answering again changes it.
- **Proposed from the write**, and accepted as 8.5's proposals are:
  - DROP, then CREATE and INSERT: Rebuilt;
  - `INSERT OVERWRITE TABLE` with no PARTITION: Rebuilt;
  - `INSERT OVERWRITE ... PARTITION (dt = <value>)`: History;
  - `INSERT INTO`, an append: History;
  - a dynamic `PARTITION (dt)` overwrite: no proposal, so the Decision waits on the user.
  A Conversion's table whose write reads itself, which has a `seed()` today, is History.
- A Rebuilt table never asks about a Seed; a History table always does (ticket 05).
- An answer may be given once under `all_tables`, a table's own overriding it.
- **Tests**: each write above gives its proposal; the dynamic overwrite leaves the Decision
  open and the step waits on it; an answer under `all_tables` and one of a table's own.
- The beginner reader runs, since the decisions cell changes.

## Answer

Built 2026-11-27.

- **Where the kind is stored, and read** (one place each, for ticket 05): a `KIND = ...` line of
  the Table reference, above its Aliases, with a comment block saying what each kind means.
  Open: `KIND = "history"  # TODO: proposed history: <why>`, or `KIND = None  # TODO: nothing
  proposed: <why>`; answered: `KIND = "rebuilt"  # answered, proposed history: <why>`, so
  check() never lists it among the lines marked `# proposed`. `decisions.KIND_LINE` is its
  pattern; `decisions.table_kind(text)` reads the answered kind (`TableKind.REBUILT` or
  `TableKind.HISTORY`, a StrEnum), None while open or where there is no KIND line;
  `decisions.proposed_kind(text)` reads the proposal; `decisions.kind_block(...)` writes it.
- **The rule**, one for convert and new_table: `converting.proposed_table_kind(ordered,
  table, database)`, from the batch's statements, and `converting.proposed_kind_of_hive(hive,
  table)`, from a write's Hive (for new_table, and for ticket 08's `to_8_10`). A write
  reading itself is History; a DROP or TRUNCATE before the first write, a CREATE ... AS or a
  query alone is Rebuilt; then an INSERT INTO is History, an INSERT OVERWRITE with no
  PARTITION Rebuilt, one with every partition column given a value History, and a dynamic
  `PARTITION (dt)` gets nothing proposed. Each comes with a one-line reason.
- **convert** writes the KIND block into each table's Table reference (`_decision_blocks`,
  after a workbook's Decisions); **new_table** writes it in `reference_from_logic`, which runs
  the logic again once the reference is written and builds `write()`: where `write()` doesn't
  build yet (no location answered), nothing is proposed, saying so. A query given in QUERIES
  is a query alone, so Rebuilt is proposed.
- **The Decision**: a new kind, `decisions.TABLE_KIND`, answered as `"kind"`: `"rebuilt"`,
  `"history"` or `"proposed"`, under a table or `all_tables` (a table's own wins; under
  all_tables, "proposed" accepts each proposal and leaves each table with none open, named in
  the report). Open until answered, so the convert and new_table decision steps wait on it; a
  proposal is pre-filled in the DECISIONS check() prints, so pasting accepts it, and a kind
  with nothing proposed for several tables is offered once under all_tables. Answering again
  changes it. write_decisions refuses a kind that is none of the three, "proposed" where
  nothing was, and a kind for a table with no KIND line (one only created, or a Table
  reference the references Workflow added). Promote refuses a table whose kind is open, as
  any open Decision.
- **Texts a beginner sees, changed**: the decisions cell's comment (every Workflow notebook),
  check()'s question and the DECISIONS lines it prints, the KIND comment in a Table reference,
  write_decisions' report and refusals, the docstrings of `write_decisions` and
  `reference_from_logic`, and how-tos 09 and 33, whose DECISIONS now answer `"kind"`.
  CONTEXT.md's Decision lists the kind.
- **Tests**: `tests/test_decisions.py` (each write shape's proposal through convert and
  check(), the dynamic overwrite open, accepting then answering again, the refusals);
  `tests/test_decisions_for_every_table.py` (all_tables' kind, a table's own over it,
  "proposed" leaving a table with none open, the step waiting on it); the journeys
  `test_convert_proposes_each_tables_kind_and_the_user_accepts_both` and
  `test_the_runner_waits_on_a_kind_nothing_was_proposed_for`, and new_table's journeys, now
  answering the kind. Every other journey and test whose script fills dt dynamically answers
  History in its decisions cell, the usability scenarios' reference ends
  (`tools/usability_scenario_files.py`) too, and the Copilot evaluation's promote tasks'
  setup cells (`PROMOTED_FROM`, `tools/copilot_eval_tasks.py`) accept the proposed kind;
  KNOWN_ACTIONS is unchanged. The Example projects, the pages
  and `tests/snapshot/known.txt` (new hashes added from the affected tests; a whole-suite
  `SNAPSHOT_WRITE=1` run on the merged branch drops the stale ones) are written again.
- **Left**: the Seed is still gated by "reads itself", not yet by the kind, which is ticket
  05's; the Example projects' tables get their kinds in tickets 07 and 08 (the intermediate
  project's workbook table, `mart.job_hours`, holds an open KIND now); a Pivot filter's
  "batch" answer, which partitions a table, keeps the kind answered before. The beginner
  reader hasn't run: this ticket's implementer spawns no agent.
- **Failing until ticket 08**: `test_the_example_projects_of_each_version_since_8_3_upgrade_
  straight_into_this_ones` for the 8.6, 8.7 and 8.8 freezes. An Upgrade from them writes the
  convert notebook again (`to_8_9`) but not the new_table, promote and references notebooks,
  whose decisions cell now names "kind", and a finished batch's `written.json` records the
  hashes of the Table references convert wrote, which now hold a KIND line. `to_8_10`, which
  writes the Workflow notebooks again and gives each table its kind, is where they match.
