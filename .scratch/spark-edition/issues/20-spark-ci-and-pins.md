# Spark CI and pins

Type: task
Status: open
Blocked by: 18, 19

## Question

Run both Editions at both ends of their ranges on every push to `dev`, as the sqlglot edition is
run today.

`.github/workflows/dev.yml` runs four jobs on Python 3.11:

- sqlglot 25.24.2 and 30.19.0: `python -m pytest`;
- pyspark 3.5.0 (or the floor ticket 2 found) and 4.0.4: install Temurin 17 with
  `actions/setup-java`, then `requirements-dev.txt` and the matrix pyspark; uninstall sqlglot and
  prove it is gone with a command that exits non-zero on its own; run
  `python -m pytest --edition spark --example-database required`.

The pin and CI tests run per Edition, reading each `engine.py`'s constants and the matrix. The
comment at `dev.yml:1-3` names both ranges. `CLAUDE.md`'s Checks and item 1 of the Definition of
done name both runs, and say to export only a commit whose four jobs passed (the export doesn't
check the galleries, and the Spark gallery's staleness test needs Java).

## Done when

The Definition of done in `CLAUDE.md` holds; all four jobs are green on `dev`; a deliberately
broken Spark query test fails the Spark job instead of skipping; `git status` is clean after a
local Spark run.
