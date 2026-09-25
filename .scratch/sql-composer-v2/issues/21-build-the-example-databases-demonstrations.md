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
- **`with_week(runs)`** in `regrouping.py` adds pandas' own week column, the Monday that
  starts each day's week, the way `week_start` does, so both pandas results read the same.

**Code review (2026-09-25), `code-review` over `11e9257..HEAD`,** with this ticket and tickets
15, 08, 10, 13, 14, 18 and 20 as the spec and `docs/agents/standards.md` as the standards. The
spec reviewer checked every number the docstrings claim against the Example database's rows and
found none wrong. Fixed in the commit after `6ed7571`:

- **Standards:**
  - "report", on the glossary's _Avoid_ list, left `left_join_then_where.py`'s title.
  - The module docstrings no longer name the executor, window functions or `NEXT_DAY`: they say
    the Example database can't run `week_start` or `row_number`.
  - `nan_in_a_list.py`'s why says `NOT IN` matches no rows, not "the test".
  - `top_runs_per_job_in_pandas()` has no backslash continuation.
- **Spec:**
  - Every pandas result's first line now says "computed in pandas, not by running this Hive",
    the label tickets 15 and 20 give, and a test in `tests/test_levels.py` holds it.
  - `careless(keeps_only_matches=True)` is shown building without the executor, so the
    sqlglot 25.24.2 run shows that opt-out working too.
  - The latest-run example's careless statuses are checked against pandas (each job's
    largest status on its own), not a typed-in list.
  - The Levels test checks that the seven named demonstrations exist, not that there are
    exactly seven Statement scripts, so the gallery's later Worked examples can join them.
  - `latest_and_top_n.py`'s why now says why you'd write it (to keep whole rows).

Answered, not changed:

- **The pandas results need sqlglot 30.19.0 too,** since `every_run()` reads the rows with a
  Statement on the Example database's `send`. Ticket 15 says an older version "can show their
  pandas reference numbers instead". The rows could be read without the executor only through
  the Example database's private names, which a Worked example must not use. The Example
  gallery is generated on `dev`, pinned to 30.19.0, and ships as HTML, so it shows the pandas
  numbers at work whatever sqlglot is there. The scripts themselves stay on `dev`.
- **The careless numbers of None in `equals` and of NaN are checked by running Hive, not
  pandas.** pandas can't give them: its `isin` treats NaN as a value, and `== None` is its own
  quirk. The test sends the careless Hive to the Example database, whose executor follows
  SQL's NULL rules, and the fixed numbers are checked against pandas.
- **"Why" explains what goes wrong,** as the prototype's model script does, since what goes
  wrong is why you'd write the fixed Statement.
- **`tests/conftest.py`'s `example_rows` reads `example_database._TABLES`,** a private name,
  so the pandas checks don't go through the executor they check. It is `dev`-only.
- **`every_run()` is written twice, and `first_day, last_day` travel together,** which
  standards.md's preference for plain repetition over machinery allows.
- **`top_runs_per_job(n=2)` keeps `n`,** since "top N" is what the ticket names.

**Beginner reader (2026-09-25).** Report:
[reports/21-beginner-reader.md](../reports/21-beginner-reader.md). Its advice is for the user.
It found every docstring number right, and one outright bug, fixed in the commit after
`ba67839`: `repeated_rows.py`'s `fixed()` joined the alerts with a plain `JOIN`, so a run that
raised no alert lost its minutes. It was right on 2026-09-24 only because every run that day
raised one; on 2026-09-23 it gave 30 minutes, not 80. It is now a `LEFT_JOIN`, and a test
runs it on 2026-09-23 too.

Its costliest stops, for the user to weigh:

- **The re-grouping Guard's "Usual fix"** says to keep the sum and the count and divide, which
  doesn't fit a distinct count, where the fix is to count again over the longer span. The
  message is `sql_composer/refusals.py`'s, so changing it is a Toolbox change.
- **A script can't be run on its own:** `python worked_examples/statements/repeated_rows.py`
  can't import `building_blocks`, and nothing prints. The gallery is where they are meant to be
  read.
- **`count_rows(where=is_not_null(job_runs.run_id))`** in `left_join_then_where.py` is what makes
  `cache_warm` show 0 rather than 1, and nothing says so.

Also noted, not changed: `top_runs_per_job(n=1)` would pick one of job 3's two 30-minute runs
at random, since nothing breaks the tie (with the default `n=2` both are kept).
