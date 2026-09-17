"""Assemble Hive SQL for closely-related business questions from declared, reusable parts.

This package exports the NOUNS a contributor types into a declarations module, plus the one
entry point that turns a Case into SQL. The VERBS stay on their modules and are reached as
`write.plan(...)`, `lineage.to_text(...)`, `verify.verify(...)` - deliberately, and for two
reasons. Three of them are called `plan` or `build`, so flattening them here would force
each to be renamed for the convenience of not typing a module name. And the module name is
the half of the call that says which concern you are in: `write.plan(registry, cases,
run_date=...)` reads as a write, `compile.plan(registry, case)` reads as a resolution, and
a bare `plan(...)` reads as neither.

    from sqlcomposer import Case, Column, Grain, Registry, Source, compile_case, by_tag
    from sqlcomposer import lineage, verify, write

Compactness was an explicit requirement of the design, and it is a count of concepts rather
than of lines. The names below are the whole vocabulary: CONTEXT.md's nouns, the aggregate
constructors that make a wrong Re-aggregation rule unspellable, and the four branches of the
refusal hierarchy - one `except` for each kind of wrongness. Everything else is one module
attribute away, and nothing is re-exported twice.
"""
from __future__ import annotations

from sqlcomposer.compile import Compiled, compile_case, escalate_sqlglot_logging
from sqlcomposer.declaration import (
    Cardinality,
    Column,
    Join,
    Registry,
    RunDate,
    Source,
    TimeBucket,
)
from sqlcomposer.errors import (
    ComposerError,
    DeclarationError,
    DriftError,
    RefusalError,
    RenderError,
)
from sqlcomposer.lineage import Lineage
from sqlcomposer.model import (
    Case,
    Dimension,
    Filter,
    Grain,
    Metric,
    ReAggregation,
    by_name,
    by_tag,
    count_distinct,
    count_of,
    count_rows,
    max_of,
    min_of,
    ratio,
    sum_of,
)

__all__ = [
    # Declarations - what the warehouse has.
    "Source",
    "Column",
    "Join",
    "Cardinality",
    "Registry",
    # The parts a question is built from.
    "Case",
    "Metric",
    "Dimension",
    "Filter",
    "Grain",
    "TimeBucket",
    "RunDate",
    # Metric constructors. There is no average_of(): a mean is a ratio, which is the fact
    # that makes it re-derivable at a coarser Grain.
    "sum_of",
    "count_rows",
    "count_of",
    "count_distinct",
    "min_of",
    "max_of",
    "ratio",
    "ReAggregation",
    # Tag families - the horizontal-scaling lever - and the escape hatch that is not one.
    "by_tag",
    "by_name",
    # Compiling.
    "compile_case",
    "Compiled",
    "Lineage",
    "escalate_sqlglot_logging",
    # Refusals, one branch per kind of wrongness.
    "ComposerError",
    "DeclarationError",
    "RefusalError",
    "RenderError",
    "DriftError",
]

__version__ = "0.1.0"
