# Spark CI and pins

Type: task
Status: resolved
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

## Answer

`.github/workflows/dev.yml` runs four jobs on Python 3.11 on every push to `dev` (`0af561a`;
reworked in `e2232e8` after its review):

- **SQL Composer** at sqlglot 25.24.2 and 30.19.0: `python -m pytest`.
- **Spark Composer** at pyspark 3.5.0 and 4.0.4, each in four steps:
  - install Temurin 17, `requirements-dev.txt` and the matrix's pyspark;
  - uninstall sqlglot;
  - prove it is gone with a command that exits 1 on its own while it can be found;
  - run `python -m pytest --edition spark --example-database required`.

The rest of the change:

- **The pin and CI tests run per Edition.** They check each Edition's own job in `dev.yml`:
  - that its pin in requirements-dev.txt is inside the range its engine.py supports, and is
    its newest tested;
  - that the job's matrix is the bottom of that range and the pin, and it installs the
    matrix's version on Python 3.11, with no continue-on-error;
  - that its last step is the test run exactly as written.

  For Spark Composer they also check Java 17, the uninstall and the sqlglot check. Each of these
  was broken on purpose in a copy (a `|| true`, a pin not from the matrix, a step in the other
  job), and a test failed each time.
- **The export's preview test** no longer needs a local `main`, which CI's checkout doesn't
  have. That was why CI had never passed on `dev`.
- **Docs.**
  - The comment at the top of `dev.yml` names both ranges and their pins.
  - CLAUDE.md's Checks names both runs and the four jobs, and says to export only a commit
    whose four jobs passed: the export checks neither gallery, and Spark Composer's needs
    Java. Item 1 of the Definition of done says the same.

**The Done-when, as it held:**

- **All four jobs green on `dev`:** run 36731747534, at `e2232e8`, and run 36729794140 at `0af561a`
  before it.
- **A Spark test that can't run fails the job, not skips:** a throwaway branch ran the same jobs
  with `SPARK_HOME=/nowhere` (run 36722317889). Both Spark jobs failed: 12 failed and 75 errors,
  each "--example-database required, but the Example database's Spark can't start". Both SQL
  Composer jobs passed. Its run before that, unbroken (36721011035), passed every test on Linux
  at both pysparks and left nothing in /tmp. The branch is deleted.
- **`git status` clean after a local Spark run:** it is, with JAVA_HOME set, and the code
  review checked it too.

## Comments

**Code review (2026-09-30), `0af561a`.** No hard violation.

- **Fixed in `e2232e8`:**
  - The workflow tests matched text anywhere in `dev.yml`, so a step in the wrong job or a
    masked exit passed. They now read each job's own lines and steps, the medium finding of
    both axes.
  - CLAUDE.md named the four versions, which no test checks. It now names only the bottom of
    each range and the pin, and item 1 of the Definition of done names the four jobs.
  - The `dev.yml` comment called the pin an end of the range. It now gives each upper limit.
  - requirements-dev.txt now says CI runs pyspark 3.5.0.
  - `_supported`'s dict of private names became an import of each engine.py.
  - The Python 3.11 check is per job.
  - `_main_commit` uses the file's own git helper.
- **Answered, not changed:**
  - A second pin reader stays in `tools/hive_corpus.py`, for sqlglot alone. The commit merged
    the test file's two, and a disagreement between the readers would fail loudly.
  - The job's id changed from `pytest` to one per Edition. No required check names the old one.

**Drift reviews.** `0af561a` and `e2232e8` were both clean.

**Beginner reader:** not run. Nothing a beginner sees changed: only CI, tests and CLAUDE.md.
