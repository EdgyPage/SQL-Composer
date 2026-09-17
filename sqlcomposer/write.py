"""Write plans: ordered statement lists that a retry converges instead of double-counting.

The library emits an ORDERED LIST of statements. An execution script runs them in sequence
and the scheduler owns retries - there is no orchestration here, no retry loop, no state.
That division is what keeps the core compile-only.

Write mode is INSERT OVERWRITE into a dated Partition, and the reason is the retry. An
INSERT INTO that runs twice double-counts, and the second run looks exactly like the first
in every log; an INSERT OVERWRITE of one Partition is idempotent, so a retry converges on
the right answer rather than compounding.

Intermediate tables are declared like any other Source, with `written_by` naming the Case
that writes them. That is what lets `plan()` order statements by dependency and what lets a
later Case re-grain their Metrics safely.

Three things this module refuses, each because the alternative is a plausible wrong number
rather than an error:

* a Partition column with no value - a dynamic Partition overwrites whatever the SELECT
  happened to produce, which on a bad day is every Partition in the table;
* a target whose non-Partition columns do not match the Case's output columns in order -
  Hive matches INSERT columns by position, so a mismatch writes the courier name into the
  fee column and reports numbers that are merely misfiled rather than missing;
* two Cases in one plan writing the same Source - they would overwrite each other's
  Partition on every run, and the survivor would depend on plan order.

Nothing here calls `.sql()`. Generation stays in `compile.render`, which is the one place
`unsupported_level=ErrorLevel.RAISE` and `warnings_are_refusals()` are applied, and the
rendered Partition literals in `Statement.partition` come back through it too.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Iterator, Mapping, Sequence

from sqlglot import exp

from sqlcomposer import compile as _compile
from sqlcomposer import lineage as _lineage
from sqlcomposer.compile import Compiled
from sqlcomposer.declaration import Column, Registry, RunDate, Source, Value
from sqlcomposer.errors import InvalidDeclaration, LiteralTypeMismatch
from sqlcomposer.lineage import Manifest
from sqlcomposer.model import Case

# `compile` and `lineage` are reached as modules rather than as imported functions on
# purpose: this module is the seam where the write path meets the read path, and a test
# that stubs `sqlcomposer.compile.compile_case` (or a future decorator on it) must be seen
# here. A `from ... import compile_case` would bind the stub-time function object forever.

__all__ = [
    "StatementKind",
    "Statement",
    "StatementPlan",
    "partition_values",
    "insert_overwrite",
    "create_table_as",
    "plan",
]


class StatementKind(Enum):
    """What a Statement does. Read by the execution script, and by nothing else."""

    SELECT = "SELECT"
    CTAS = "CTAS"
    INSERT_OVERWRITE = "INSERT_OVERWRITE"


@dataclass(frozen=True)
class Statement:
    """One finished SQL string plus what a human needs to know before running it.

    `sql` is a complete statement with no placeholders and no parameters - the external API
    this library targets takes one finished string, and the scheduler does not itself
    substitute values into SQL text. Both of those are recorded assumptions rather than
    facts the user supplied; do not deepen the dependency on them silently.

    `purpose` is one line for a run log. `partition` is the Partition this statement
    overwrites, as ordered (column, rendered literal text) pairs, so an operator can see
    what a retry will replace without parsing the SQL.

    The literal text is the literal exactly as it appears in the SQL, quotes included
    (`("dt", "'2026-01-02'")`), because the question it answers is "what will this
    statement replace" and the answer has to be comparable with the statement itself.
    """

    kind: StatementKind
    sql: str
    target: str | None
    purpose: str
    partition: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class StatementPlan:
    """An ordered list of statements and the Manifests the writes produce.

    Order is a dependency order, not a convenience: a Case reading a Source that another
    Case in the same plan writes must run after it. Iterating yields the statements, so an
    execution script is `for statement in plan: runner.run(statement.sql)`.

    `manifests` carries one Manifest per write, in the same order as the writes appear in
    `statements`. A Manifest is what lets a later Case trace through the written table to
    the true upstream Sources, so it is emitted with the statement that creates the reason
    for it rather than reconstructed afterwards.
    """

    statements: tuple[Statement, ...]
    manifests: tuple[Manifest, ...] = ()

    def __iter__(self) -> Iterator[Statement]:
        return iter(self.statements)

    def __len__(self) -> int:
        return len(self.statements)

    def to_script(self) -> str:
        """The statements as one `;`-separated script, each preceded by its purpose as a
        comment. For pasting into a scheduler that takes a file rather than a list.

        A convenience, and deliberately a lossy one: the script drops `kind`, `target` and
        the Partition pairs, so anything that needs to reason about a statement should
        iterate the plan instead of parsing this back. An empty plan renders as the empty
        string rather than a lone newline, so writing it to a file cannot leave a script
        that looks like it contains something.
        """
        blocks = []
        for statement in self.statements:
            comment = "\n".join(f"-- {line}" for line in statement.purpose.splitlines())
            blocks.append(f"{comment}\n{statement.sql};")
        if not blocks:
            return ""
        return "\n\n".join(blocks) + "\n"


# --------------------------------------------------------------------------------------
# The target table, and the Partition a write lands in.
# --------------------------------------------------------------------------------------


def _write_target(registry: Registry, case: Case, *, operation: str) -> Source:
    """The Source a Case writes to, as the Registry declares it.

    Resolved through the Registry rather than trusted from `Case.writes_to` so that the
    columns this module checks against are the same Declaration `Registry.schema()`,
    `native_grain()` and the Drift check use. A `writes_to` naming a Source nobody declared
    raises `UndeclaredSource` here, which is the earliest anything catches it: `freeze()`
    checks a written Source against its producing Case, but only for Sources it holds.
    """
    if case.writes_to is None:
        raise InvalidDeclaration(
            subject=f"case:{case.name}",
            problem=f"{operation} needs a target table, but Case {case.name!r} declares no "
            "`writes_to`",
            remedy=f"give the Case `writes_to=<Source>` and give that Source "
            f"`written_by={case.name!r}`, or compile it as a read with compile_case()",
        )
    return registry.source(case.writes_to.qualified)


def _partition_literal(
    target: Source,
    column: Column,
    value: Value,
    *,
    run_date: date,
    defaulted: bool,
) -> exp.Expr:
    """One Partition value as an AST node, through the target column's own `Column.literal`.

    Bare literal, never a CAST: `PARTITION(dt = CAST('2026-01-02' AS DATE))` defeats
    partition pruning on every subsequent read of the table, and `Column.literal` is the
    method that knows a Partition column renders differently for that reason.

    Two wrinkles a caller meets here rather than in `Column.literal`:

    The run date is handed over as a `RunDate`, not as a `date`. `Column.literal` refuses a
    hand-written `date` against a text-typed column - correctly, because a STRING column
    compared to a DATE is NULL in Hive and the row vanishes - but admits a date that came
    from a `RunDate`, since `dt STRING` holding `yyyy-MM-dd` is the standard Hive shape.
    A dated Partition IS that case, so the default is translated into the library's own
    deferred form instead of being refused. Only a date equal to the run date is
    translated; an override of `partition={"dt": date(...)}` for some other day against a
    text column is still refused, and the idiom for it is `RunDate() - 1`.

    A default the column cannot hold at all - the run date against `region STRING` is
    rendered, but against `region BIGINT` is not - is reported as a Partition column left
    without a value, because that is the actionable form of it: supply one.
    """
    subject = f"{target.qualified}.{column.name}"
    if value is None:
        raise InvalidDeclaration(
            subject=subject,
            problem=f"Partition column {column.name!r} of {target.qualified} was given no "
            "value",
            remedy=f"pass partition={{{column.name!r}: <value>}}; an INSERT OVERWRITE with "
            "a dynamic Partition overwrites whatever the SELECT produced, which on a bad "
            "day is every Partition in the table",
        )
    if isinstance(value, date) and not isinstance(value, datetime) and value == run_date:
        value = RunDate()
    try:
        return column.literal(value, run_date=run_date, subject=subject)
    except LiteralTypeMismatch as mismatch:
        if not defaulted:
            raise
        raise InvalidDeclaration(
            subject=subject,
            problem=f"Partition column {column.name!r} of {target.qualified} is declared "
            f"{column.type}, which cannot hold the run date, and no value was supplied "
            "for it",
            remedy=f"pass partition={{{column.name!r}: <value>}} with a value matching "
            f"{column.type}",
            declared_type=column.type,
        ) from mismatch


_PartitionSpec = tuple[tuple[Column, Value, exp.Expr], ...]
"""Each Partition column of the target, its value, and that value as an AST node. The one
place the default and the overrides are reconciled, so `partition_values` and
`insert_overwrite` cannot disagree about which Partition a statement targets."""


def _partition_spec(
    target: Source,
    *,
    run_date: date,
    partition: Mapping[str, Value] | None = None,
) -> _PartitionSpec:
    """Reconcile the run-date default with the supplied overrides, in declared order."""
    supplied = dict(partition or {})
    declared = {column.name: column for column in target.partition_columns}
    unknown = sorted(set(supplied) - set(declared))
    if unknown:
        raise InvalidDeclaration(
            subject=f"source:{target.qualified}",
            problem=f"{', '.join(unknown)} is not a Partition column of "
            f"{target.qualified}",
            remedy="name a declared Partition column, or mark the column "
            "`partition=True` in the Declaration if the warehouse partitions by it",
            declared=", ".join(declared) or "(the table declares no Partition column)",
        )
    spec: list[tuple[Column, Value, exp.Expr]] = []
    for column in target.partition_columns:
        defaulted = column.name not in supplied
        value = run_date if defaulted else supplied[column.name]
        node = _partition_literal(
            target, column, value, run_date=run_date, defaulted=defaulted
        )
        spec.append((column, value, node))
    return tuple(spec)


def partition_values(
    registry: Registry,
    case: Case,
    *,
    run_date: date,
    partition: Mapping[str, Value] | None = None,
) -> tuple[tuple[str, Value], ...]:
    """The Partition a write of this Case targets, in the target Source's declared order.

    Defaults every Partition column of `case.writes_to` to `run_date`, which is the common
    shape (`PARTITION(dt = '2026-01-02')`) and the reason a retry converges. `partition`
    overrides or adds values for Partition columns that are not dates.

    Raises `InvalidDeclaration` when a Partition column is left without a value, because an
    INSERT OVERWRITE with a dynamic Partition overwrites whatever the SELECT happens to
    produce - which on a bad day is every Partition in the table. A column is left without
    a value when it is given `None` explicitly, or when the run-date default cannot inhabit
    its declared type and no override was supplied.

    Every value is rendered here and the rendering thrown away, so a value that cannot
    inhabit its column refuses at this call rather than several steps later inside
    generation. A target that declares no Partition column at all returns `()`: the write
    then overwrites the whole table, which still converges on a retry.
    """
    registry.require_frozen("write.partition_values")
    target = _write_target(registry, case, operation="partition_values")
    return tuple(
        (column.name, value)
        for column, value, _node in _partition_spec(
            target, run_date=run_date, partition=partition
        )
    )


# --------------------------------------------------------------------------------------
# Statements.
# --------------------------------------------------------------------------------------


def _check_positional_contract(target: Source, output_names: Sequence[str]) -> None:
    """Refuse a target whose body columns do not match the Case's outputs, in order.

    Hive matches INSERT columns by position and checks nothing else, so a target declaring
    `(courier, attempts, failures)` against a Case producing `(courier, failures,
    attempts)` writes every number into the wrong column and reports them without
    complaint. Partition columns are excluded from the comparison: their values come from
    the PARTITION clause, never from the SELECT, and a Declaration is free to list them
    first or last.
    """
    body = tuple(column.name for column in target.columns if not column.partition)
    if body != tuple(output_names):
        raise InvalidDeclaration(
            subject=f"source:{target.qualified}",
            problem=f"{target.qualified} declares its non-Partition columns as "
            f"({', '.join(body) or 'none'}), but the Case producing it outputs "
            f"({', '.join(output_names)})",
            remedy="regenerate the Declaration for the written table, or align the Case's "
            "Grain and Metric names with it; Hive matches INSERT columns by position, so "
            "the order is the contract",
            declares=", ".join(body) or "(none)",
            outputs=", ".join(output_names),
        )


def _write_purpose(case: Case, target: Source, rendered: Sequence[tuple[str, str]]) -> str:
    """One log line naming the Case, the table and the Partition a retry would replace."""
    if rendered:
        where = "PARTITION(" + ", ".join(f"{name} = {text}" for name, text in rendered) + ")"
    else:
        where = "(whole table; it declares no Partition column)"
    return f"Case {case.name!r} -> INSERT OVERWRITE TABLE {target.qualified} {where}"


def _insert_statement(
    registry: Registry,
    case: Case,
    *,
    run_date: date,
    partition: Mapping[str, Value] | None,
    target: Source,
) -> tuple[Statement, Compiled]:
    """The INSERT OVERWRITE, and the Compiled read it wraps.

    `plan()` needs the `Compiled` for its `CasePlan`, which is what a Manifest is derived
    from; `insert_overwrite()` throws it away. Compiling once for both is not just an
    optimisation - compiling twice would resolve the Tag family twice, and a Metric
    declared between the two resolutions would put a column in the Manifest that is not in
    the statement.
    """
    spec = _partition_spec(target, run_date=run_date, partition=partition)
    compiled = _compile.compile_case(registry, case, run_date=run_date)
    _check_positional_contract(target, compiled.plan.output_names)

    arguments: dict[str, object] = {
        "this": target.to_sqlglot(),
        # A copy, because embedding an expression re-parents it: the tree on `Compiled`
        # would silently become a child of this INSERT and stop rendering as a statement.
        "expression": compiled.ast.copy(),
        "overwrite": True,
    }
    if spec:
        arguments["partition"] = exp.Partition(
            expressions=[exp.column(column.name).eq(node) for column, _value, node in spec]
        )
    rendered = tuple((column.name, _compile.render(node)) for column, _value, node in spec)
    return (
        Statement(
            kind=StatementKind.INSERT_OVERWRITE,
            sql=_compile.render(exp.Insert(**arguments)),
            target=target.qualified,
            purpose=_write_purpose(case, target, rendered),
            partition=rendered,
        ),
        compiled,
    )


def insert_overwrite(
    registry: Registry,
    case: Case,
    *,
    run_date: date,
    partition: Mapping[str, Value] | None = None,
) -> Statement:
    """`INSERT OVERWRITE TABLE db.tgt PARTITION(dt = '...') SELECT ...`.

    Built as `exp.Insert(this=<table>, expression=<select>, overwrite=True,
    partition=exp.Partition(expressions=[...]))`. Each partition value is rendered through
    the target column's own `Column.literal`, so it is a bare literal and not a CAST -
    `PARTITION(dt = CAST('2026-01-02' AS DATE))` defeats pruning on every subsequent read of
    the table.

    The SELECT's column order is `Case.output_names`: Dimensions in Grain order, then
    Metrics sorted by name. Hive matches INSERT columns by position, so that order is a
    contract between this function and the target table's Declaration, and it is why
    `output_names` must stay stable. This function checks that contract rather than
    trusting it: a target whose non-Partition columns differ from the outputs, in name or
    in order, raises `InvalidDeclaration`.

    The SELECT embedded here is the gated, qualified tree `compile_case` produced, so the
    statement reads INSERT OVERWRITE TABLE mart.tgt PARTITION(...) SELECT `t`.`a` AS `a`
    ... - backtick-quoted inside the SELECT and bare on the target, because `qualify()`
    only ran on the SELECT. That asymmetry is cosmetic, and golden SQL is written
    against it.

    Raises `InvalidDeclaration` when `case.writes_to` is None.
    """
    registry.require_frozen("write.insert_overwrite")
    target = _write_target(registry, case, operation="insert_overwrite")
    statement, _compiled = _insert_statement(
        registry, case, run_date=run_date, partition=partition, target=target
    )
    return statement


def create_table_as(registry: Registry, case: Case, *, run_date: date) -> Statement:
    """`CREATE TABLE db.tgt AS SELECT ...`.

    For creating an intermediate Source the first time, and for a test fixture. Not the
    write path: a CTAS is not idempotent, so a retry fails on an existing table rather than
    converging, and production writes are `insert_overwrite`.

    Two consequences of that, both deliberate. There is no `partition` argument: Hive's
    CTAS cannot create a partitioned table, so a target that declares Partition columns
    needs real DDL and this statement would create a flat table of the wrong shape - which
    the first `insert_overwrite` then fails on, loudly, rather than writing anything wrong.
    And the positional check `insert_overwrite` runs is not run here, because a CTAS takes
    its column names from the SELECT rather than matching them to a declaration.

    Raises `InvalidDeclaration` when `case.writes_to` is None: without a target there is no
    table to create, and guessing a name from the Case would invent a Source no Declaration
    carries.
    """
    registry.require_frozen("write.create_table_as")
    target = _write_target(registry, case, operation="create_table_as")
    compiled = _compile.compile_case(registry, case, run_date=run_date)
    # `.ctas()` copies the Select rather than mutating it, but the tree on `Compiled` is
    # handed back to the caller, so copy anyway and keep that independent of sqlglot.
    statement_ast = compiled.ast.copy().ctas(target.to_sqlglot())
    return Statement(
        kind=StatementKind.CTAS,
        sql=_compile.render(statement_ast),
        target=target.qualified,
        purpose=f"Case {case.name!r} -> CREATE TABLE {target.qualified} AS SELECT "
        "(creation only; a retry fails on the existing table)",
    )


# --------------------------------------------------------------------------------------
# Ordering a set of Cases.
# --------------------------------------------------------------------------------------


def _dependency_order(registry: Registry, cases: Sequence[Case]) -> tuple[Case, ...]:
    """Topologically sort by `written_by` dependency, ties broken by Case name.

    Lexicographic rather than layered: whenever several Cases are ready, the alphabetically
    first runs next. That makes the order a pure function of the Cases, so two runs of the
    same plan produce byte-identical scripts and a diff of a generated script shows only
    real changes.

    The dependency edge is `Case A reads a Source that Case B in this same list writes`.
    Sources written by a Case outside the list are not edges - that table already exists
    and its write is somebody else's schedule.
    """
    by_name: dict[str, Case] = {}
    for case in cases:
        if case.name in by_name:
            raise InvalidDeclaration(
                subject=f"case:{case.name}",
                problem=f"Case {case.name!r} appears twice in one statement plan",
                remedy="pass each Case once; a plan is an ordered list of statements, and "
                "two entries for one Case would run its write twice",
            )
        by_name[case.name] = case

    written: dict[str, str] = {}
    for case in cases:
        if case.writes_to is None:
            continue
        qualified = case.writes_to.qualified
        earlier = written.get(qualified)
        if earlier is not None:
            raise InvalidDeclaration(
                subject=f"source:{qualified}",
                problem=f"Cases {earlier!r} and {case.name!r} both write {qualified}",
                remedy="give one of them a different `writes_to`; two Cases writing one "
                "Partition overwrite each other every run, and which numbers survive "
                "depends on the order of this list",
            )
        written[qualified] = case.name

    blockers: dict[str, set[str]] = {name: set() for name in by_name}
    for case in cases:
        for source in case.sources(registry):
            producer = written.get(source.qualified)
            if producer is not None and producer != case.name:
                blockers[case.name].add(producer)

    ready = [name for name, blocking in blockers.items() if not blocking]
    heapq.heapify(ready)
    remaining = {name: set(blocking) for name, blocking in blockers.items()}
    ordered: list[Case] = []
    while ready:
        name = heapq.heappop(ready)
        ordered.append(by_name[name])
        del remaining[name]
        for other in sorted(remaining):
            if name in remaining[other]:
                remaining[other].discard(name)
                if not remaining[other]:
                    heapq.heappush(ready, other)
    if remaining:
        raise InvalidDeclaration(
            subject=f"plan:{', '.join(sorted(remaining))}",
            problem="these Cases each read a Source another of them writes, so no order "
            "of statements produces correct numbers for all of them",
            remedy="break the cycle by reading the atomic Source in one of them, or split "
            "the plan across two scheduled runs",
            cycle=", ".join(sorted(remaining)),
        )
    return tuple(ordered)


def _overrides_per_case(
    targets: Mapping[str, Source],
    partition: Mapping[str, Value] | None,
) -> dict[str, Mapping[str, Value] | None]:
    """Split one `partition` mapping across targets that partition by different columns.

    A plan can write two Sources with different Partition columns, so the mapping is
    filtered per target rather than handed to each write whole - otherwise
    `partition={"region": "eu"}` would refuse against the target that has no `region`.
    The typo protection is kept by checking the mapping against the union: a key that is a
    Partition column of no target in the plan still refuses.
    """
    if not partition:
        return {name: None for name in targets}
    unused = set(partition)
    split: dict[str, Mapping[str, Value] | None] = {}
    for name, target in targets.items():
        declared = {column.name for column in target.partition_columns}
        matched = {key: value for key, value in partition.items() if key in declared}
        unused -= set(matched)
        split[name] = matched or None
    if unused:
        raise InvalidDeclaration(
            subject="plan:partition",
            problem=f"{', '.join(sorted(unused))} is not a Partition column of any Source "
            "this plan writes",
            remedy="check the spelling, or drop the key; a Partition value that lands "
            "nowhere would leave that Partition defaulted to the run date in silence",
            writes=", ".join(sorted(target.qualified for target in targets.values()))
            or "(this plan writes nothing)",
        )
    return split


def plan(
    registry: Registry,
    cases: Sequence[Case],
    *,
    run_date: date,
    partition: Mapping[str, Value] | None = None,
) -> StatementPlan:
    """An ordered plan for a set of Cases, with the writes ordered by dependency.

    A Case whose Sources include a Source written by another Case in the same list runs
    after it. The order is a topological sort of that dependency graph, broken ties by Case
    name so two runs of the same plan produce the same script. A cycle - two Cases each
    reading a Source the other writes - raises `InvalidDeclaration`.

    Cases with `writes_to` become INSERT OVERWRITE statements and contribute a Manifest;
    Cases without become plain SELECTs, which is how a plan can end with the query whose
    numbers a human actually wants.

    `partition` applies to every write, filtered per target to the Partition columns that
    target declares - a plan writing a daily table and a daily-by-region table takes one
    mapping. A key that matches no target in the plan refuses, so the filtering never
    swallows a typo.

    The whole plan is compiled before any of it is returned, so a refusal in the last Case
    is raised before an execution script has run the first statement. That ordering is the
    point of a compile-only core: the expensive failure is a half-written warehouse, not a
    failed build.
    """
    registry.require_frozen("write.plan")
    ordered = _dependency_order(registry, cases)
    targets = {
        case.name: _write_target(registry, case, operation="write.plan")
        for case in ordered
        if case.writes_to is not None
    }
    overrides = _overrides_per_case(targets, partition)

    statements: list[Statement] = []
    manifests: list[Manifest] = []
    for case in ordered:
        target = targets.get(case.name)
        if target is None:
            compiled = _compile.compile_case(registry, case, run_date=run_date)
            statements.append(
                Statement(
                    kind=StatementKind.SELECT,
                    sql=compiled.sql,
                    target=None,
                    purpose=f"Case {case.name!r} -> SELECT at {case.grain}",
                )
            )
            continue
        statement, compiled = _insert_statement(
            registry,
            case,
            run_date=run_date,
            partition=overrides[case.name],
            target=target,
        )
        statements.append(statement)
        manifests.append(_lineage.manifest_for(registry, compiled.plan, target))
    return StatementPlan(statements=tuple(statements), manifests=tuple(manifests))
