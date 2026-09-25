# Build the Example database's demonstrations

Type: task
Status: claimed
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

## Comments

**Build decisions (2026-09-25), where the tickets left something open.** Each picks the most
beginner-readable option; the user may overturn any of them.

- **The seams under test** are each script's own functions, `careless()`, `fixed()` and the
  `..._in_pandas()` results, run through the public `run(..., send=example_database.send)`,
  plus the import statements the Levels test reads. The pandas checks read the Example
  database's rows directly (`conftest.example_rows`), not through its `send`, so they don't
  rely on the executor they check.
- **The seven scripts** in `worked_examples/statements/`: `repeated_rows.py`,
  `regrouping.py`, `left_join_then_where.py`, `none_in_equals.py`, `nan_in_a_list.py`,
  `not_equals_drops_null.py` and `latest_and_top_n.py`. Two Building blocks in
  `worked_examples/building_blocks/`: `alerts_per_run.py` (the prototype's) and
  `jobs_per_day.py`, the daily Building block the re-grouping example adds up by the week.
- **Scripts import the Toolbox only from its top level** (`from sql_composer import ...`, then
  `job_runs = example_database.job_runs`), as the Toolbox's own docstring asks, and their
  Building blocks as `from building_blocks.x import x`, with `worked_examples/` on pytest's
  path.
- **`careless()` takes the opt-out it would need,** defaulting off: `careless()` is what most
  people write first, and it refuses or warns; `careless(adds_up=True)`,
  `careless(keeps_only_matches=True)` or `careless(many_matches=True)` pastes the opt-out and
  shows the wrong number. The keyword is the Guard's own, so nothing new is named.
- **Guards with no opt-out** (None in `equals`, NaN): `careless()` refuses, and its docstring
  says what Hive would have given (0 rows). The test proves it by sending the fixed
  Statement's Hive with `IS NULL` turned back into `= NULL`, or the NULL put back into the
  `NOT IN` list, straight to `example_database.send`.
- **NaN is shown in `is_not_in` with a list from a DataFrame with a blank cell,** where a NULL
  makes `NOT IN` match nothing at all: the most visible wrong number (0 runs, not 3), and the
  way a NaN usually reaches a Statement.
- **Re-grouping shows one distinct count, days to weeks, with `week_start`:** adding up each
  day's count of jobs gives 6 for the week, when 3 jobs ran. An average of averages is left
  out, so the example has one wrong number to read. Since the executor has no `NEXT_DAY`,
  `careless_in_pandas()` and `fixed_in_pandas()` give the results. Their test also teaches the
  executor `NEXT_DAY` and `DATE_ADD` for that test only, and shows the Hive gives the same
  numbers as pandas.
- **Pandas results are functions named after the Statement they stand for,** with `_in_pandas`
  added (`fixed_in_pandas()`, `top_runs_per_job_in_pandas()`), each saying in its first line
  that it is "computed in pandas, not by running its Hive". They read the rows with a plain
  Statement the Example database can run (`every_run()`), then do the week or the numbering
  in pandas.
- **Latest run per job gets a `careless()` too,** since there is a wrong number to show:
  `max_of` on each column takes each status from a different run (job 2's newest run FAILED,
  and it shows SUCCESS). No Guard catches it. `fixed()` is the latest run per job with
  `row_number`, and `top_runs_per_job(n=2)` the top N per group, the two longest runs.
- **`not_equals` has no Guard,** so its test shows both Statements build quietly, and checks
  3 against 4 with pandas' own `!=`.
- **The Levels test** (`tests/test_levels.py`) reads every import in `building_blocks/` and
  `statements/`: a lower Level, the Toolbox from its top level, the standard library, pandas,
  numpy or sqlglot, and nothing else. It also checks that each Statement script's docstring
  has a title of at most 80 characters and a one-sentence "Why: " paragraph, the shape the
  gallery reads. ruff now checks `worked_examples/` too.
