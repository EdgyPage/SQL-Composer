# The rounds: file 20 tuned, held-out scored, the code path scored

Type: task
Status: open
Blocked by: 09, 10, 11, 12, 13
Size: L

## Question

Whether both paths reach the bar (round 3, Q9; "Both paths, equal").

## Done when

- **The Copilot path**: file 20 tuned on dev for at most two rounds, then the held-out split
  scored once on Haiku and Sonnet; 95%, or a design spec of what misses.
- **The code path**: the same tasks converted by `project.convert`, scored by the same scorer,
  with each run's Workbook check; every miss fixed or written up as a bug.
- **A manual round** in Copilot on the workbooks the user builds in Excel, kept in
  `.eval-local/`.
- Each round recorded in the ledger; results in `.eval-local/`, never in git.
