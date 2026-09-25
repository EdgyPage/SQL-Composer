# Build the Example database's demonstrations

Type: task
Status: open
Blocked by: 18

## Question

Write the demonstrations decided in "What does the Example database demonstrate, and where does it
run?", on the `sql_composer/example_database.py` that "Build the Toolbox core" ships.

- **Seven Statement scripts** in `worked_examples/statements/`, with any Building block they need
  in `worked_examples/building_blocks/`:
  1. repeated rows (the Warning);
  2. re-grouping;
  3. `LEFT_JOIN` then `WHERE`;
  4. `None` in `equals`;
  5. NaN;
  6. `not_equals` dropping NULL rows;
  7. latest run per job and top N per group with `row_number`.

  Each has a module docstring giving a title and one sentence on why, plus `careless()` and
  `fixed()` where there is a wrong number to show. The prototype's `repeated_rows.py` on
  `prototype/example-database` is the model.
- **One `dev` test per script:**
  - it asserts the careless and fixed numbers against a pandas check;
  - it shows the Guard refusing, or the Warning firing, and the opt-out working;
  - executor-backed tests skip with a reason below sqlglot 30.19.0.
- **Pandas results:** for `row_number` and `week_start`, which the executor can't run, give the
  result computed in pandas, labelled as such, for the gallery to show.

Done when the Levels test covers `worked_examples/`, every script's test passes, and the
definition of done in "What does `dev` enforce, and which maintainer agents does it carry?" is
met.
