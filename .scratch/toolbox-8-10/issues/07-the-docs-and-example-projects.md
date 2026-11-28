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

- **Also fixed**: the pages' stand-in for today (`tools/example_gallery.example_setting`)
  replaced `conditions.today`, so a Seed's run as of each day (`conditions.run_as_of`) gave
  2026-09-25 on the page and how-to 34's Seed read "reads no today" there while its doctest
  passed: it now pins `conditions.utc_now`, as the tests do; the gallery is unchanged by it.
  The Copilot evaluation's control `makes_the_prod_copy_but_never_writes_it` leaves out the
  whole write step, since the Seed alone now loads the prod copy's days.
- **Snapshot**: `SNAPSHOT_WRITE=1` writes only from a whole, passing suite, which the
  upgrade test waiting on ticket 08 blocks, so the 192 texts a whole run made and it lacked, some from tickets 02 to 06, were added to
  `tests/snapshot/known.txt` from the hashes a run made; the stale ones stay until 08's
  whole-suite write.

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

## Beginner reader

Run 2026-11-28 on how-to 34 and the texts 8.10 changed, at 0db88e08; the user: fix "All 24".
Each stop, fixed or answered (the report stays local; behaviour fixes test-first):

- **A** (stuck; 7 repeats it) fixed, behaviour: check(query=) reads a History table's
  Partitions only when it has a Seed (an Original, or a write that reads today), so
  mart.job_day_facts, whose day is typed in, is passed over, never "Not checked"; check()'s
  docstring example names mart.job_day_events. Tests:
  `test_check_project_passes_over_a_history_table_that_has_no_seed` and
  `tests/test_check_open_kinds.py`.
- **B** (stuck; 11 repeats it) fixed, behaviour: to_8_10 asks a History table with no SEED
  with nothing proposed, `SEED = {}  # TODO: nothing proposed: project.upgrade() reads no
  Partitions, ...`, as spec 05 proposes the months form only where SHOW PARTITIONS finds a
  column of dates; `decisions.asked_seed_block` is gone; an open SEED's question names the
  months form. mart.budget_overruns (region alone) shows it.
- **C** (stuck; 14 repeats it) answered and reworded: last_n_days does read today (the Seed
  loads the logic again under `run_as_of`); the no-Seed message, seed_tables' docstring and
  how-to 34 step 3 name last_n_days and Run values, and warn off Python's date.today().
- 1 fixed: seed_tables' first line no longer leans on "History table" and "Seed".
- 2 fixed: convert's docstring says each History table is seeded by seed_tables in the write
  step.
- 3 fixed: convert's example DECISIONS shows its "kind" line whole.
- 4 fixed: "with none" spelled out (no partition columns, no Original); "the months before
  today".
- 5 fixed: "one calendar month back from the newest", with dates, in docstrings, SEED's
  comment, messages, how-tos 09 and 34, the README, Copilot file 17 and CHANGES.
- 6 fixed: seed_tables' docstring shows a Seed's first and last report lines.
- 8 fixed: equals' docstring shows `equals(job_runs.status, 1)`.
- 9 fixed: how-to 34's Goal defines each word in a list, one at a time.
- 10 fixed: how-to 34 step 1 says what `conn` is.
- 12 answered: how-to 34 step 2 says what `# TODO:`, `# answered,` and `# proposed` mean; with
  B fixed no `# TODO: proposed` is left.
- 13 fixed, behaviour: check() names each kind and Seed left open in a Table reference, saying
  only promote waits on them and where to answer; how-tos 10, 28, 32 and 34 show it, and 28
  says why 8.10's line is "nothing to change by hand".
- 15 answered: how-to 34 step 4 and When you'd use it: "rebuilt" takes the SEED line out.
- 16 answered: why `repr(...)`, in steps 2 and 6.
- 17 fixed, behaviour: a Seed run as of each past day never runs as of today, which is the
  first write's run, so no day is written twice (an append would have doubled it); its first
  line names the dt days and "each run as of the day after". 31 days now, not 32.
- 18 fixed: step 7 shows the cell's three lines, create() first.
- 19 fixed: step 7's report is one report; the run-of-days line is shown as another table's.
- 20 answered: step 8 says check() reads only a table admin/sent.csv records as written.
- 21 fixed: Rebuilt table, History table and Seed in NOTEBOOK_TERMS, so each Workflow
  notebook's Terms define them.
- 22 fixed: promote's write step has its own PROD_SEED_ACTION (the dev copy's original, else
  the dev copy).
- 23 answered: a dev table's kind goes in admin/check_project.ipynb with
  project.write_decisions(...), or the next Workflow notebook naming it, never promote's cell
  (to_8_10's checklist, CHANGES, README).
- 24 fixed: CHANGES says any Project from 7.1 on upgrades straight to 8.10.

Choices the specs didn't settle: 17's rule (the Seed leaves today's run to the first write,
for a table with no partition columns too) and 13's check() block (kind and Seed only, every
Table reference, one short line each). The copied Seed (with an Original) is unchanged.
