# Beginner reader: ticket 12, the Example database leaves the library

Run 2026-11-13 by the `beginner-reader` agent (model opus), on the diff since 96ec3d0a at
a95b6a43, before the fixes listed at the end. Advisory only; the user decides what changes.

## What it read

1. `run_query` and `run_execute` (`sqlglot_composer/running.py`).
2. `UNION_ALL` (`stacking.py`) and `latest_partition` (`run_values.py`).
3. The `warehouse.py` Template (`WAREHOUSE_TEXT`, `project.py`): its docstring, `connect`'s
   docstring and its two refusals.
4. `project.build_run` and `project.add_references`.
5. The README's Terms entry "Example database" and step 4, "Read a Worked example".
6. How-to 01's paragraph "This page connects to the Example database".

## What it reported

The common thread: `job_runs`, `run_alerts`, `query` and `execute` now appear in examples with
nothing that `help()` shows saying where they come from. Only the README and the Example
gallery say it.

1. **running.py.**
   - "here it reads the Example database" (slows): on main, "here" points at nothing to run,
     and `job_runs` is used without a definition.
   - `run_execute`'s `execute:` output is explained two paragraphs later (minor).
2. **Stacking and latest_partition.**
   - `UNION_ALL`, `UNION`, `INTERSECT` and `EXCEPT` use `run_alerts` and `job_runs` with
     nothing defining them (slows). The removed `run_alerts = ...` line used to say what it was.
   - `latest_partition`'s second block imports from `references` and `warehouse`, which
     answered the question.
3. **warehouse.py.** "such as your team's conn, in connect(conn)" reads oddly, `conn` is
   unexplained, and it differs from the notebook comment's wording (slows).
4. **build_run and add_references.**
   - `build_run` imports everything but `job_runs` (slows).
   - `add_references` uses `query=query` right after `project.start()` said to connect, with
     no `connect` (slows).
   - `compare_batch`'s output names the Example database (minor).
5. **README.**
   - Terms: "what it gave on them" reads oddly (minor).
   - Step 4: the bullet "its `query` and `execute` in the place of yours" has the direction
     backwards (slows).
   - Outside the sample (blocks): line 18, steps 5 and 2's `import example_database` /
     `connect(example_database)`, and the shipped Example projects' setup cells, all fail on
     main with `ModuleNotFoundError`.
6. **How-to 01.** "It doesn't ship with the Toolbox: your notebook connects to your own
   warehouse here." is followed straight away by `>>> import example_database`, without saying
   to leave that line out (slows).

Its top three suggestions:

1. Fix main's `import example_database` lines in the README and the shipped Example projects.
2. Say once, where `help()` reaches it, whose `jobs`, `job_runs`, `query` and `execute` are.
3. Word the connection as "connect(conn), where conn is your team's connection".

## What was done

- **Suggestion 2, done.** `sqlglot_composer/__init__.py`'s docstring, which
  `help(sqlglot_composer)` shows, now says it once. Each name's own docstring is left alone,
  since the ticket says the examples lose their import lines.
- **Suggestion 3, done.** `connect`'s docstring and both refusals now read "such as
  connect(conn), where conn is your team's connection". So does how-to 01's copy.
- **How-to 01, done.** It now says to leave the two lines out in your own notebook and to
  connect as above.
- **README Terms and step 4's bullet, done.** They now read "what it gave when run on them" and
  "standing in for yours".
- **Suggestion 1, left for ticket 13.** It reworks the README's tutorial to be read, not run,
  and replaces main's `example_projects/` with a page.
- **`run_query`'s "here" and `compare_batch`'s printed text, left as they are.** The Example
  database is still what the examples ran on.
