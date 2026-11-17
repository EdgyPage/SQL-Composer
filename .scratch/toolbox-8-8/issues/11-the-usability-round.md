# The usability round

Type: task
Status: open
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
