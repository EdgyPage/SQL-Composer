# The usability round

Type: task
Status: resolved
Blocked by: 12
Size: M

## Question

Can a zero-context user schedule a run from what main ships?

## Done when

- **Inputs recorded and memoized** (the user, 2026-11-09: "start documenting and memoizing
  the inputs ... so we can reduce token counts and speed up test times"):
  - each run writes `_loop/inputs.json`: the scenario, dev's commit, a hash of each file of
    main's tree the scenario's phases name or the run reads, the scenario's own files, and
    each phase message, and the row in results.md names that hash;
  - `prepare` builds main's tree once per commit into a cache in the loop's temp folder and
    copies it, and sets up a scenario's warehouse once per (commit, scenario);
  - a scenario whose inputs hash matches a run that passed is reported as memoized, with that
    run named, and isn't given to an agent again unless asked (`--fresh`);
  - `tests/test_usability_loop.py` builds main's tree once per session, not per test;
  - `docs/usability-loop.md` says what is cached, where, and how to clear it.
- A scenario in `tools/usability_scenario_files.py`: from the intermediate Project, a run of a
  table's weekly breakdown, parameters given as text, run top to bottom.
- A round of it and W1, three runs each, on 8.6 as it ships, recorded in results.md with what
  it found.

## Answer

### The loop's memoized inputs (built 2026-11-09)

The first two "Done when" bullets are built; the round itself is still to run.

- **What is hashed.** `_loop/inputs.json` holds the scenario, dev's commit, and a SHA-256 of
  each thing an agent is given: main's whole tree (`main.tree`) and each file of it the
  phases' messages name (`main.named`, found by `main/<path>` in the text, the README in
  every one); the Project brought in, file by file, before its connection is filled in, but
  for its copy of the Toolbox, which is main's; the team's warehouse as set up; every file of
  the scenario's folder, its key among them, so a changed key isn't memoized by an old pass;
  each phase's message, written for the placeholders `<run>` and `<python>` so every run's is
  the same; and the loop's files put in a run (the runner, the warehouse's code, the team's
  connection text). `tools/usability_loop.py` itself is not hashed: a change to `score` is
  checked by re-scoring a kept run, not by giving agents the scenario again.
- **Why the whole tree, not only the named files.** An agent reads any how-to it finds, so a
  hash of the named files alone would memoize a scenario past a fix to the how-to it read.
  The commit is left out of `inputs_hash` instead: a commit that changes nothing main ships
  (`tools/`, `.scratch/`, tests) keeps every scenario memoized.
- **The export's stamp.** version.txt and the README say when the export ran and from which
  commit; `main_file_hash` leaves that stamp out, or no two builds would ever match.
- **Determinism.** A Project made by another scenario's reference end (W5, from W2) is made
  under `times_pinned()`, as the scenarios' build makes it, so its files hash the same each
  time; checked by preparing W5 twice, which gave the same hash, and by finding no path of
  the cache in the copied Project.
- **The cache.** `prepare` builds main's tree once per commit into
  `<temp>/usability-loop/cache/main/<commit>/` (about 18 s and 5 MB at 8.6), and sets up each
  scenario (its files, its warehouse, its Project before connecting) once per commit into
  `cache/scenarios/<commit>/<scenario>-<hash>/`, the hash that of the scenario's own files, any
  dev folder its Project is copied from and the scenario it starts from, so an uncommitted
  edit to a scenario is never served stale. Each is built into a folder of its own and
  renamed, so a build cut short is never taken for a whole one (made safe for prepares at
  once by the code review, below). Building a new commit's tree
  drops every other commit's cache, which keeps the folder small; delete it to clear it.
  `--main` is gone: the cache does its job. With no cache (the tests), each is made afresh in
  a temporary folder, by the same code.
- **Memoized means a round's worth.** The ask was "a run that passed has the same inputs";
  a round gives a dev scenario three runs and a held-out one one, so a scenario is memoized
  once that many runs passed with its inputs and none failed. One pass alone would stop runs
  2 and 3 of the round that made it, and a failure beside a pass means the docs aren't yet
  enough.
- **`plan` and `--fresh`.** `usability_loop.py plan <scenario> ...` prints, per scenario,
  `memoized` with its runs named, or `run it` with why (no run recorded, 2 of 3 passed, a
  run failed), working the inputs out from the cache as `prepare` does. `prepare` refuses a
  memoized scenario, naming its runs, before it makes the folder; `--fresh` runs it anyway.
- **Where the hash is read.** `record` ends the row's note `inputs <16 hex>`, and `plan`
  reads results.md's rows, so a row moved into a round's section still counts; a row from
  before 8.6 names no inputs and memoizes nothing. The kept run's `_loop/inputs.json` has the
  whole record.
- **The tests.** `tests/test_usability_loop.py` builds main's tree once per session
  (`built_main`), for the two tests that need a real tree; the cache's test stands
  `build_main` in with a fake that counts its builds. New tests: the inputs file, the same
  for two runs and changed by a file of main or of the scenario; the Project hashed without
  its Toolbox; the stamp left out of main's hash; the cache building main once per commit and
  each scenario once, each run a copy of its own, another commit's cache dropped; `plan`'s
  answer for three, two, a failure and none, and one pass for a held-out scenario; and
  `record` naming the hash, with `prepare` refusing until `--fresh`.

#### The code review (2026-11-09)

- **Two prepares at once were unsafe.** `cached_main` and `cached_scenario` each built into
  one `<name>.building` folder, removing any there first, so a second prepare could delete
  the first's build part way through; and `drop_other_commits` could remove a cache another
  prepare was copying from. Now one helper, `build_in_place`, builds into a folder of its own
  call's (`tempfile.mkdtemp` beside the place), renames it into place, and discards its own
  when the place is there already or another build reached it first; both caches use it. And
  `hold_the_cache` holds the cache's lock, `cache/prepare.lock`, a folder made with `mkdir`,
  removed in a `finally`, while `prepare` (and `plan`) works out its inputs, builds, drops and
  copies the run, so dropping never runs while another prepare holds the cache. A prepare
  that finds it held waits up to `LOCK_WAIT` (five minutes), then refuses with a
  `TimeoutError` naming the lock and saying to delete it if no prepare is running. Standard
  library only, and offline. Tests: two threads racing `build_in_place` on one place, each
  part way through when the other is, leave one whole folder and nothing beside it; a held
  lock refuses a prepare that would drop another commit's cache, which stays, and a lock held
  a moment by another thread is waited for, then the other commit dropped and the lock gone.
  `docs/usability-loop.md` says prepares may run at once, and what to do if the lock is held.
- **Names.** `the_inputs` gives a `RunInputs` NamedTuple (`inputs`, `main_tree`, `set_up`),
  not a 3-tuple read by `[0]`, and `prepare` no longer reassigns its parameter `main`. `place`
  named both main's tree and a scenario's set-up: each is named for what it holds,
  `main_tree` and `set_up`, through `make_the_run`, `set_up_the_scenario`,
  `bring_in_the_project` and `inputs_of`. `drop_other_commits` iterates plainly, unsorted.
- **`inputs_of`** had four jobs: the scan for main's files the messages name is its own
  function, `named_main_files`.
- **The team's connection** was hashed as `TEAM_CONNECTION + TEAMS_CONN + TEAMS_CONNECT`
  joined: each is hashed on its own now, the two sets of lines given a Project under their
  own keys in `loop_files`. This changes every scenario's `inputs_hash`; no run had recorded
  one yet.
- **From the drift review.** The doc said a scenario's cache folder's hash is that of its own
  files; `scenario_hash` covers the folder its Project is copied from and the scenario it
  starts from too, and the doc and the module's docstring say so now. And `run_notebook.py`
  with `--cells` that left out the cell tagged parameters dropped `-p`'s parameters without a
  word: it refuses now, naming the tagged cell and saying to add it to `--cells`, with a test.

**The scenario, W8**, "a Scheduled run of a week's breakdown, its week given as text", a dev
scenario for a technical user, from the intermediate Example project as `my_project/`:

- **The job.** Make `team_week` with the Toolbox; the scheduler gives it `WEEK`, a day of the
  week to add up, as text (2026-09-16); each run writes mart.team_days for each day of WEEK's
  week, Monday to Sunday, and no other day, each table it reads written for those days first,
  then gives back week_totals; build it and read its Hive, then run it top to bottom with
  `run_notebook.py ... -p WEEK 2026-09-16`.
- **Why a past week.** The Example database holds 2026-09-11 to 2026-09-24, and each Table
  notebook's `write()` writes the last 3 days ending 2026-09-24. A run of the latest week
  would pass with week_totals alone, the build adding each `write()`; the week of 2026-09-16
  passes only if WEEK reaches every table's `write_days`, the case how-to 31's "Expecting a
  parameter to move the tables the build adds" is about.
- **The answer key** checks the table written, mart.team_days, holding exactly 2026-09-14 to
  2026-09-20's rows, worked out by an independent Hive query over the ops tables (as every W
  key is), and two files: the run's notebook, holding `WEEK`, and the registry's
  `scheduled_run,team_week` row, so it was made by `new_scheduled_run`. The SELECT's rows come
  back only in the run's `results`, which no file keeps, so the key checks the table instead;
  week_totals reads nothing else, so a right table is a right breakdown.
- **Its warehouse** has the three mart tables created, empty, as each Table notebook's step 1
  creates them (`tables_made.hql`).
- **`-p` in the runner.** A scheduler passes parameters as text, papermill with `-p NAME
  VALUE`, into a cell after the one tagged `parameters`; `run_notebook.py` had no way to, so
  it gains `-p NAME VALUE`, which runs `NAME = 'VALUE'` right after the tagged cell, and
  refuses a notebook with no tagged cell. W8's job names it; the other scenarios' messages
  are unchanged.
- **Its reference end** makes the run, types its two cells (WEEK, and `write_days` of the
  three tables before week_totals), and runs it with the runner, WEEK given as text. The
  Project's Templates have the team's connection already, so the new notebook needs none.
  In-process, a Project from before 8.6 (H2's) leaves its run's folder first on Python's
  path, so the reference end runs the notebook with no other run's `team_connection.py` on
  it, as a scheduler's own Python would.

### The round (2026-11-09)

- W1 and W8, three fresh Haiku runs each, on main's tree built from dev at 8.6 (e2776efc),
  prepared one at a time: **6 of 6 passed, no question asked**. Recorded in
  `.scratch/usability-loop/results.md`'s "The 8.6 round", each row ending with its inputs
  hash; afterwards `plan W1 W8` answers memoized for both, so the next round gives neither to
  an agent until an input changes.
- Found, none failing a run, listed there for a later round: the README's Scheduled runs never
  name `write_days` for a run of a chosen period, nor that a write in `statements()` takes the
  place of the one the build adds; parameter defaults and `run_value` against reading the
  parameter unsaid; W1's 8.5 frictions again; and the harness: the runs' agents share the
  session's scratchpad.
