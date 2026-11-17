# The usability round

Type: task
Status: resolved
Blocked by: 10
Size: M

## Question

Can a zero-context user, from what main ships, find why a number moved (Q18)?

## Done when

- **A new dev scenario, W10**: a stand-in user is told `mart.team_report`'s fail rate moved
  with no change to its notebook, and finds, from `admin/lineage.ipynb` and the difference
  page, the upstream change it comes from and when the table was next written. Its
  `reads.json` names what its path reads.
- The round runs only what the plan says changed, as `docs/usability-loop.md` says, and only
  when the user asks for it; its records stay in `.eval-local/`.
- Its findings are fixed in the docs, or recorded for the next version, in this ticket.

## Answer

Built and run 2026-11-17, the user's goal "implement 8.8" asking for it.

- **W10**, `tools/usability_scenarios/W10/`, built by `usability_scenario_files.lineage_scenarios`:
  from the intermediate Example project as it ends, a technical user is told mart.team_days'
  runs changed though its notebook didn't, and writes `my_project/answer.md` naming the file
  that changed, the table whose own logic it changed and when that table was first written
  with it (key: `events_per_job`, `mart.job_day_facts`, `2026-09-25 08:00`). Its reads: the
  README's "7. Follow lineage" and how-tos 32 and 7. Its reference end exports the difference
  for mart.team_days and writes the answer from the twin, and passes its key.
- **The first round: W10 alone**, `2026-11-17-W10-1`, on Haiku: pass, no question, 5 actions,
  65,791 tokens.
- **The 8.8 round**, the user's "Run the round" (2026-11-17), after the beginner reader's
  wording fixes: every scenario, since the Toolbox folder and the README's top changed with
  8.8, the held-out ones (E4, H1, H2) at the raise. Runs `2026-11-17-<id>-1`, 38 agents on Haiku
  with the rerun below, about 2.16M tokens, in the ledger and `.eval-local/usability/`.
  - **Passed first time, 15 of 16:** W1 to W10 and H1, H2 with no question (H2 upgraded an 8.0
    Project to 8.8); E2, E3, E4 with the one Copilot question the Excel path asks.
  - **E1 failed:** asked for `mart_dev.job_run_report`, its converter named the one-file batch
    for its final Table, `job_report`, as "Have Copilot write it" step 6 said ("so name the
    batch for its final Table"), and made `mart_dev.job_report`. Fixed in bd89b7e6 and
    e2bd39b2: steps 3, 5 and 6 say to name the file, or a batch of one file, for the table you
    want, its final Table's name unless you were asked for another (step 3 from
    `tools/workflow_graph.py`, which writes it).
  - **E1 again**, `2026-11-17b-E1-1`: pass, one question; its converter named the file and the
    batch `job_run_report` from the README.
  - **Two test fixes the round showed:** the scenario reference-end test prepares each run
    fresh, since a held-out scenario that passed at this version is memoized and `prepare`
    refuses it; the Workflows page test holds step 3's new words.
- **Friction the stand-ins reported, recorded for the next version** (no run was stopped by it):
  `project.check()` from a plain script needs the Project folder and `connect(...)` first, which
  the docs don't say; a converted Table reference's two TODO lines go unmentioned by the
  convert steps; no documented way to list the original's Partitions; a Windows path with
  backslashes in the connection lines; the new table notebook's cell 3 refused before
  new_table's reference step has run; `run_notebook.py --list` numbers code cells only.
