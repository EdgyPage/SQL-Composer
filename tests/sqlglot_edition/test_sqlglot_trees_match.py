"""The Toolbox's own trees behave as the sqlglot trees SQL Composer builds from them.

Over every calculation, condition and sort key in the Hive corpus, a Node and its sqlglot tree
(`writing.to_sqlglot`) agree on the order of their columns, on equality, on whether they add
rows up, on what an AND in ON= joins, and on a window's partition columns. The lineage and the
Guards rest on these. A hive_function call is the one declared exception: the Toolbox walks and
compares it as written, where sqlglot may have rewritten it.
"""

from __future__ import annotations

import warnings

import pytest
from sqlglot import exp

import hive_corpus_cases
from sql_composer import GuardRefused, LoadRefused, writing
from sql_composer.clauses import derived_tables
from sql_composer.trees import has_aggregate


def _trees_of(s) -> list:
    found = [column._tree for column, _ in s._outputs]
    found += [c._tree for c in s._where + s._having]
    found += [read.on._tree for read in s._reads if read.on is not None]
    return found + [c._tree for c in s._group_by] + list(s._order_by)


def _corpus_trees() -> list:
    found = []
    for _, build in hive_corpus_cases.edge_cases() + hive_corpus_cases.generated_cases():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # some cases join off a key, which warns
                statements = build()
        except (GuardRefused, LoadRefused, TypeError, ValueError):
            continue
        for s in statements:
            if s._ddl is None:
                for step in [s] + [table._statement for table in derived_tables(s)]:
                    found += _trees_of(step)
    return found


TREES = _corpus_trees()
# The trees whose columns sqlglot might have rewritten: those holding a hive_function call.
AS_WRITTEN = [any(True for _ in tree.find_all("HiveFunction")) for tree in TREES]


def test_the_corpus_has_trees_of_every_shape() -> None:
    kinds = {node.kind for tree in TREES for node in tree.walk()}
    assert len(TREES) > 1000
    assert {"And", "Or", "Paren", "Case", "Window", "Call", "HiveFunction", "Between", "In",
            "Not", "Coalesce", "Distinct", "Ordered"} <= kinds


@pytest.mark.parametrize("index", range(len(TREES)))
def test_a_tree_matches_its_sqlglot_tree(index: int) -> None:
    node = TREES[index]
    tree = writing.to_sqlglot(node)
    if not AS_WRITTEN[index]:
        assert ([(c.table, c.name) for c in node.find_all("Column")]
                == [(c.table, c.name) for c in tree.find_all(exp.Column)])
    assert has_aggregate(node) == writing._adds_rows_up(tree)
    if node.kind == "And":
        assert ([writing.hive_text(part) for part in node.flatten()]
                == [writing.sql_text(part) for part in tree.flatten()])
    windows = zip(node.find_all("Window"), tree.find_all(exp.Window))
    for mine, theirs in windows:
        assert ([c.name for c in mine.parts["partition_by"] if c.kind == "Column"]
                == [c.name for c in theirs.args.get("partition_by") or []
                    if isinstance(c, exp.Column)])


def test_two_trees_are_equal_exactly_when_their_sqlglot_trees_are() -> None:
    chosen = [tree for tree, written in zip(TREES, AS_WRITTEN) if not written][:400]
    built = [writing.to_sqlglot(tree) for tree in chosen]
    for first in range(len(chosen)):
        for second in range(first, len(chosen)):
            assert ((chosen[first] == chosen[second]) == (built[first] == built[second])), (
                writing.hive_text(chosen[first]), writing.hive_text(chosen[second]))
