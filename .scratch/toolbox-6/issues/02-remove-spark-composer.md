# Remove Spark Composer

Type: task
Status: open
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

- `git grep -i spark` on dev finds only the ADRs, CHANGES.md's history and the .scratch tracker.
- The export ships one Toolbox and checks nothing Spark-shaped.
- The pytest runs pass, the code-review skill has run with this ticket as its spec, its drift
  items are closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's
  Definition of done).
