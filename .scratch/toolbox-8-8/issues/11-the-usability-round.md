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
- **The round: W10 alone**, one run, `2026-11-17-W10-1`, on Haiku: **pass**, no question, 5
  actions, 65,791 tokens, 62 s, in the ledger and `.eval-local/usability/`. Its user found
  the difference page the Example project had exported, named all three, and checked the state
  current with `project.check()`. No finding to fix.
- **Not run:** the other scenarios, which `plan` would run again since the Toolbox folder and
  README changed with 8.8, and the held-out scenarios (E4, H1, H2), due once at a version's
  raise. Each is a round of its own, which only the user starts (`docs/usability-loop.md`).
