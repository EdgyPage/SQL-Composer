"""The Edition's output, pinned: its golden corpus in `tests/hive_corpus/`.

`tools/hive_corpus.py` writes, for each case under a stable id, what the Toolbox shows through
its public names: each Statement's Hive, the repr of its outputs and conditions, the commands
`write_table_reference`, `check_table_reference` and `check_key` send, and `export_lineage`'s
Markdown report. The cases are every docstring example and Worked example that builds a
Statement, the edge cases in `hive_corpus_cases.py`, and about 200 generated ones.

This test fails while the committed file differs from what the Edition writes today. Write it
again only for a change that is meant to alter the output; `tests/repo/test_edition_parity.py`
then holds the two Editions' files to each other.
"""

from __future__ import annotations

import pytest

import hive_corpus


@pytest.mark.skipif(hive_corpus.cannot_write() is not None,
                    reason=str(hive_corpus.cannot_write()))
def test_the_committed_golden_is_what_the_toolbox_writes_today() -> None:
    golden = hive_corpus.GOLDEN
    committed = golden.read_text(encoding="utf-8") if golden.exists() else ""
    assert hive_corpus.corpus_text() == committed, (
        f"tests/hive_corpus/{golden.name} differs from what the Toolbox writes today. If the "
        f"change is meant, run {hive_corpus.COMMAND} and review the diff."
    )
