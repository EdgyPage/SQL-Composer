# Remove Spark Composer

Type: task
Status: resolved
Blocked by: -
Size: L

## Question

Map Notes, "Spark and the one Toolbox". Tag `last-spark-composer` on dev's last two-Edition
commit first. Then remove `spark_composer/`, `tests/spark_edition/`,
`tests/hive_corpus/spark_composer.txt`, the `spark-composer` CI job, Spark's sections of
`requirements.txt` and `requirements-dev.txt` (and the pyspark warning filters in
`pyproject.toml`), `--edition` and `--example-database` from `tests/conftest.py`, every Spark
branch in shared tests and in `tools/` (`how_to_page.py`, `example_gallery.py`,
`example_project.py`, `hive_corpus.py`, `export_clean.py`), and Spark's rules in
`tools/offline_policy.py`. The README template loses its Spark sections. Write the ADR that
supersedes 0002 (why, and the tag to recover it from).

## Done when

- `git grep -i spark_composer` and `git grep "Spark Composer"` on dev find only the ADRs,
  CHANGES.md's history, the README's note for Spark Composer's users, the .scratch tracker, and
  the tests' stand-in for an old copy; Spark itself stays named where a user's own send may run
  the Hive on Spark.
- The export ships one Toolbox and checks nothing Spark-shaped.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).

## Answer

Built in `fa8682a`, reworked after the review in the commit that resolves this ticket, on the
branch `toolbox-6/02-remove-spark-composer`. The tag `last-spark-composer` (on `1d7f198`, before
anything was removed) holds both Editions; ADR 0008 supersedes ADR 0002.

- Removed: `spark_composer/`, `tests/spark_edition/`, Spark's golden corpus, the parity tests
  (`test_edition_parity`, `test_how_to_parity`, `test_writers_agree`), Spark's CI job,
  requirements and pyspark warning filters, `--edition` and `--example-database`,
  `DECLARED_DIFFERENCES`, the name swap and `editions.use`, the how-tos' Edition blocks and the
  how-to page's `[only]` rendering, and Spark Composer's sections of the README template.
- Moved: the offline trap every test run installs, from `spark_composer/engine.py` to
  `tests/offline_trap.py`, with its `ALLOWED` entry. The user approved moving the entry in the
  session on 2026-10-20 ("Move it").
- Kept for ticket 03: `tools/editions.py` with one Edition, the Composer core, and the "Edition"
  wording that goes with them.
- Done ahead of ticket 03: CLAUDE.md names the toolbox-6 map, and the drift reviewer's `parity`
  kind and standards.md's Parity section went, both being about two Editions.

### Review answers

- Spec (a)1, the pyspark rules left in `tools/offline_policy.py` (`pyspark.install`, Spark
  Connect, `spark.jars.packages`): kept on purpose. They aren't Spark Composer's code but guards
  that refuse network-reaching pyspark calls anywhere in the repo; dropping them would weaken the
  offline policy, which only the user changes.
- Spec (a)2-3, Done when's grep: the dated `docs/offline-audit.md` (with a 6.0 note at its top)
  and the "dropped in 6.0" notes in CLAUDE.md, CONTEXT.md, the drift reviewer and
  `tools/editions.py` also name Spark Composer, on purpose. The first Done when line was widened
  by the implementer during the work, which the user should know.
- Beginner reader: how-to 27's missing blank line (a broken doctest) fixed; how-to 27's goal,
  `hive_function`'s docstring, the README's note for Spark Composer users and the glossary's
  two-Edition lines reworded. Open for the user: a Spark-only user can't create a Saved table
  with a Key, since Spark refuses `PRIMARY KEY`, and the README's Spark section says what differs
  but not what to do about it.
