# The references Workflow proposes and checks

Type: task
Status: open
Blocked by: 07
Size: M

## Question

About 8 runs stopped on a Table reference's TODO lines, and about 7 typed `check_key` lines to
choose a Key (map, Q14, Q15).

## Done when

- `add_references` writes "what one row is" proposed from the Key, "One row per run_id.",
  `# proposed`, and leaves it a TODO with no Key; and `does_not_add_up` proposed from each
  column's name and type (`avg_*`, `*_ratio`, `*_pct`, `*_rate`, a double `*_per_*`), `# proposed`.
- Its Key step proposes a Key per table, from the columns DESCRIBE gives and one count of
  distinct values per likely id column through the user's query, runs `check_key` on it, and
  prints each verdict and the DECISIONS line to accept it.
- A proposal is accepted as a Key is (07), and project.check() names a `# proposed` line left.
- Journeys: references with no `check_key` typed and no TODO line edited.

## Answer
