# The rounds: file 20 tuned, held-out scored, the code path scored

Type: task
Status: open
Blocked by: 09, 10, 11, 12, 13, 17
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

## Comments

- At ticket 10's merge (2026-11-19), the code path on the 40 pivot tasks, scored by
  `excel_eval.score` as ticket 05's test scores its own: 32 pass; X90, X92, X102, X110, X111,
  X113, X119 and X120 don't, among them X90's running total's grand total (PV8), X92's
  calculated item added into its total not named (PC3's mark words), X102's summary Table
  `team_report` read from the database, and X119's Data Model Distinct Count. Each is a code
  or reference bug for this ticket to settle, both paths equal (ADR 0016).
