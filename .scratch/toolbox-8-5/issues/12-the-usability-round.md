# The usability round

Type: task
Status: resolved
Blocked by: 11
Size: M

## Question

Did the zero-context users' actions fall? (map, Q1).

## Done when

- `usability_loop` scores a run's actions too (cells edited, files written, calls from no cell),
  from its Project, beside its cells added.
- A round of W1, W3, W7 and H1 on main's tree as 8.5 ships, three runs each, recorded in
  results.md against 8.4's, with what it found.

## Answer
Built 2026-11-06.

- `usability_loop.count_actions`: each Workflow notebook's code cells a run edited from as the
  Toolbox writes them, and each file it wrote of its own (outside its Project, or a script
  saved for a Workflow), reported as the run's actions and carried in its row's note; they
  fail nothing (`RunScore.edited_cells`, `own_files`, `actions`).
- The round: W1, W3, W7 and H1, three runs each, on 8.5 as it ships, all 12 passed with no
  question; results.md's "The 8.5 round" holds it against 8.4, with what it found. Two
  findings were mended after it (the run cell's text on running to the end; promote's
  location line); the rest are listed there for a later round.
- It ran after ticket 13, not before: the version is in what a user reads, so the round ran on
  8.5 exactly as it ships.
