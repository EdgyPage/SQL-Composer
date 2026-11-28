# The docs and the Example projects

Type: task
Status: resolved
Blocked by: 01, 02, 03, 04, 05, 06
Size: M
Spec: [specs/07-the-docs-and-example-projects.md](../specs/07-the-docs-and-example-projects.md)

## Question

Teach Rebuilt and History tables and the Seed, and show them in the Example projects (round 4,
Q2 and Q3).

## Done when

- **A new how-to 34, "Load a History table's past days"**: the kind Decision and its proposal,
  `"seed": {"months": N}`, and the Seed's report, worked on the intermediate Example project.
  Its page in `docs/main/` written by its tool.
- **How-tos 06 and 09** each point to it in a line; anything they say that tickets 02 and 03
  made untrue (adding a reference first, a compare that stops the batch) is put right.
- **Copilot files 06 and 07** each gain a line on the kind Decision, each still under 9,000
  characters; `copilot/all_in_one/all_copilot_files.txt` merged again.
- **The Example projects**: every table has its kind, as `to_8_10` writes it, and one daily
  table of the intermediate project shows `"seed": {"months": 1}`, for how-to 34. No new
  tables.
- The Workflows overview page and the Example projects page written again by their tools.
- The beginner reader runs on how-to 34 and the changed how-tos.
- **Usability**: one dev scenario (a converter whose batch holds a History table whose date
  Hive computes), run only on the user's yes, as `docs/usability-loop.md` says.

## Answer

Built 2026-11-27.

- **How-to 34, "Load a History table's past days"** (Intermediate), on a copy of the
  intermediate Example project: each table's KIND and SEED lines read (answered and open);
  a new daily table, mart.job_day_events, made with new_table, its write reading
  `last_n_days(job_events.dt, 1)`; `reference_from_logic(query=query)` writing its KIND open
  (nothing proposed, PARTITION (dt)) and SEED proposed `{"months": 1}`; the kind and seed
  answered with write_decisions; the Seed's dry run (2026-08-24 to 2026-09-24, each day run
  as of the day after) and mart.job_day_facts's "reads no today" refusal of one; the Seed's
  report at work, with a day not loaded and a day with no rows, and check_project's Warning,
  shown in prose, since the Example database can't be written; `project.check(query=query)`
  run, naming mart.job_day_facts not checked. Its page written by `tools/how_to_page.py`.
- **How-tos 06, 08, 09 and 29** point to it. 08's step 3 runs `project.check(query=query)` and
  says what check_project's Warning is; 09's all_tables section names "kind"; 29's prose
  (written by `tools/workflow_graph.py`) says a failed compare stops nothing and what kind and
  the Seed are. promote's report's Next line (`project._promote_next_line`) said "seed each
  that reads itself": now "then write each, each History table's Seed first".
- **README template**: section 6's Table reference and write steps name KIND, SEED and
  seed_tables; section 8 names check_project's Warning; section 9's Decisions name the kind and
  the months form of the Seed, and "Run the rest" seeds each History table.
- **Copilot files**: 06 R11 and 07 R9, the kind Decision (06 trimmed to fit, 8,990 with Windows
  line breaks; 07, 8,987); 16 R7, a History prod copy's Seed as ticket 05 built it; 17's Seed
  term, R6, R9 (`{"months": N}`, a P15 row), R11, W3 (the write step's seed_tables) and its
  steps 4 to 6; written by `tools/copilot_files.py` (01 too, for check's `query=`) and merged.
  The eval keys FAILS_COMPARED, T41, T42, T48 and T49 send `project.seed_tables(...)` in
  place of the old seed cells; T48's prompt accepts its proposed kind.
- **Example projects**: each source Table reference gains its KIND block, as to_8_10 would
  write it from the table's exported Hive (`converting.proposed_kind_of_hive`): answered where
  a kind is proposed (budget_overruns History, job_notes Rebuilt); open, `KIND = None`, where
  nothing is (every PARTITION (dt) write: job_day_costs, job_events_checks, team_days,
  team_failures and all four of the starter's). mart.job_day_facts is answered History by
  hand, with `SEED = {"months": 1}`. mart.job_hours's kind is accepted in the convert
  decisions cell (`"kind": "proposed"`, Rebuilt, "it is a query alone"). Both READMEs say so.
  Both projects, docs/main/example_projects.html, examples.html and how_to.html written again.

For ticket 08:

- to_8_10 must write the KIND blocks exactly as the sources hold them (kind_block's comment,
  `answered, ` in place of `TODO: `, above the Aliases, or at the end where a reference has
  none, as team_failures's). GAINED_BY_HAND["8.10"] needs, for the intermediate:
  references/mart__job_day_facts.py (answered by hand, SEED), references/mart__job_hours.py
  and its checklist and admin/removed/ copy (its reason is the batch's, "a query alone", where
  its Hive alone gives "names no Partition"), and both READMEs.
- **A History table with no SEED line breaks seed_tables**: `seeding.seed_lines` imports SEED
  once open_decisions passes, so mart.budget_overruns (History, answered as to_8_10 would,
  no SEED) raises ImportError in a dry run, or in prod after a promote, where it holds no
  Partition. to_8_10 should write a SEED for each History table, or seed_lines treat none as
  "no Seed". Not fixed here.
- The Workflow notebooks' decisions-cell comment and "Run the rest" cell (workflows.py) still
  say a table that reads itself is seeded and a failed compare stops the run.

Left: the beginner reader and the usability scenario haven't run (this implementer spawns no
agent); CHANGES.md and the version are ticket 08's.
