"""SQL Composer's output, pinned: the golden corpus in `tests/hive_corpus/sql_composer.txt`.

Tickets 10-13 of the PySpark work (`.scratch/spark-edition/`) move the Toolbox's insides off
sqlglot's trees, and nothing a user sees may change. `tools/hive_corpus.py` writes, for each case
under a stable id, what the Toolbox shows through its public names: each Statement's Hive, the
repr of its outputs and conditions, the commands `write_table_reference`,
`check_table_reference` and `check_key` send, and `export_lineage`'s Markdown report. The cases
are every docstring example and Worked example that builds a Statement, the edge cases in
`hive_corpus_cases.py`, and about 200 generated ones.

This test fails while the committed file differs from what the Toolbox writes today. Write it
again, with `python tools/hive_corpus.py`, only for a change that is meant to alter the output.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import sqlglot

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import hive_corpus  # noqa: E402


@pytest.mark.skipif(
    sqlglot.__version__ != hive_corpus.PIN,
    reason=f"the golden is written at the sqlglot pin, {hive_corpus.PIN}; "
    f"this is {sqlglot.__version__}",
)
def test_the_committed_golden_is_what_the_toolbox_writes_today() -> None:
    golden = hive_corpus.GOLDEN
    committed = golden.read_text(encoding="utf-8") if golden.exists() else ""
    assert hive_corpus.corpus_text() == committed, (
        "tests/hive_corpus/sql_composer.txt differs from what the Toolbox writes today. If the "
        "change is meant, run python tools/hive_corpus.py and review the diff."
    )
