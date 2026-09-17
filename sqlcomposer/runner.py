"""The Runner protocol and the execution entry point. Convenience only.

The core is compile-only: it returns statements plus Lineage and never executes anything.
Nothing in `errors`, `declaration`, `model`, `joins`, `grain`, `compile`, `lineage`, `write`
or `verify` imports this module, and that is a structural property worth keeping - a test
that asserts it is cheap and catches the day someone reaches for a connection inside the
compiler.

A `Runner` is injected by the caller. It takes ONE finished SQL string, because the external
query API this library targets takes one finished string rather than `(sql, params)`, and
because the scheduler does not itself substitute values into SQL text. Both of those are
recorded assumptions rather than facts the user supplied - a `Runner` that quietly grew a
`params` argument would deepen the dependency on them without anyone deciding to.

pandas is imported under TYPE_CHECKING only, so `import sqlcomposer.compile` stays free of
it. Nothing here touches a pandas symbol at runtime either: the one frame operation this
module performs (`frame()`'s rename) goes through the returned object's own methods, so the
module imports and runs with pandas absent right up until a Runner hands one back.

Three behaviours here are not visible in the signatures, and all three exist so that a
failure looks like a failure rather than like a plausible answer:

* a `runner` with no `run()` is refused BEFORE the first statement goes out, so a typo in
  the caller's wiring cannot leave a plan half-written;
* a `run()` that returns `None` is refused, because `list[pandas.DataFrame]` containing a
  `None` blows up in the caller's `concat` a long way from the cause;
* the exception from a failing statement propagates unchanged, with a `__notes__` entry
  naming which statement failed and what already ran.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Sequence, runtime_checkable

from sqlcomposer.compile import Compiled
from sqlcomposer.write import Statement, StatementKind, StatementPlan

if TYPE_CHECKING:
    import pandas

__all__ = ["Runner", "execute", "execute_plan", "frame"]


@runtime_checkable
class Runner(Protocol):
    """Whatever the caller uses to talk to the warehouse.

    One method, taking one finished SQL string. No parameters, no dialect argument, no
    connection lifecycle - the library builds a string and hands it over, and everything
    about how it is executed belongs to the caller.

    `runtime_checkable` so a test can assert an object satisfies it, but note that a
    Protocol's runtime check verifies the method exists and nothing about its signature.
    That is enough for the check this module actually wants - "did the caller pass the
    thing they meant to pass" - and no substitute for the caller's own tests of their
    Runner.
    """

    def run(self, sql: str) -> pandas.DataFrame:
        """Execute one statement and return its rows.

        A statement that returns nothing (an INSERT OVERWRITE) should return an empty
        DataFrame rather than None, so a caller can treat every result the same way. This
        module enforces that: a `None` is a `TypeError` naming the statement, not a `None`
        smuggled into a list annotated `list[pandas.DataFrame]`.
        """
        ...


def _require_runner(runner: object, *, called: str) -> None:
    """Refuse a non-Runner before anything is executed.

    Cheap, and it buys the guarantee that matters: without it, a caller who passes a
    connection instead of their Runner wrapper discovers the mistake as an `AttributeError`
    raised from inside the loop - which, on statement three of five, means three writes
    have already happened. Checked once at the top of each entry point instead.
    """
    if not isinstance(runner, Runner):
        raise TypeError(
            f"sqlcomposer.runner.{called}() needs a Runner - any object with "
            f"run(sql: str) -> pandas.DataFrame - but got "
            f"{type(runner).__name__}, which has no run(). Nothing was executed."
        )


def _require_frame(result: object, *, what: str) -> None:
    """Refuse a `None` result, naming the statement that produced it.

    The single most likely Runner bug is `def run(self, sql): self.cursor.execute(sql)` -
    correct-looking, and it returns `None` for every statement. Left alone it produces a
    `list[None]` from a function annotated `list[pandas.DataFrame]`, and the traceback
    surfaces wherever the caller first touches a frame.
    """
    if result is None:
        raise TypeError(
            f"Runner.run() returned None for {what}. Return an empty DataFrame for a "
            "statement with no rows (an INSERT OVERWRITE) so every result can be treated "
            "the same way."
        )


def _headline(statement: Statement, *, index: int, total: int) -> str:
    """`statement 2 of 5: write delivery health` - the position a human needs first."""
    return f"statement {index + 1} of {total}: {statement.purpose}"


def _describe(statement: Statement, *, index: int, total: int) -> str:
    """One human-readable block naming a statement by position and purpose.

    Deliberately does NOT include the SQL. The caller already holds the statement list and
    this names the index into it; pasting a multi-kilobyte statement into an exception note
    buries the one line - the purpose - that says what was being attempted.
    """
    lines = [_headline(statement, index=index, total=total) + " FAILED"]
    lines.append(f"  kind:      {statement.kind.value}")
    if statement.target is not None:
        lines.append(f"  target:    {statement.target}")
    if statement.partition:
        rendered = ", ".join(f"{column} = {value}" for column, value in statement.partition)
        lines.append(f"  partition: {rendered}")
    return "\n".join(lines)


def _already_ran(statements: Sequence[Statement], *, index: int) -> str | None:
    """What a human needs to know about the statements that succeeded before this one.

    The operator's next question after a mid-plan failure is always "can I just run it
    again". For a plan of SELECTs and INSERT OVERWRITEs the answer is yes, and that is the
    whole reason decision 5 chose INSERT OVERWRITE into a dated Partition: a re-run
    overwrites the same Partition and converges instead of double-counting. A CTAS breaks
    that - it fails on the table it already created - so this says so rather than offering
    reassurance that is only true most of the time.
    """
    if index == 0:
        return None
    done = statements[:index]
    span = "statement 1" if index == 1 else f"statements 1-{index}"
    created = [s.target or "?" for s in done if s.kind is StatementKind.CTAS]
    if created:
        return (
            f"  already ran: {span}, including a CTAS of {', '.join(created)}. A CTAS is "
            "not idempotent; drop that table before re-running the plan."
        )
    return (
        f"  already ran: {span}. Every one is a SELECT or an INSERT OVERWRITE of a dated "
        "Partition, so re-running the whole plan converges rather than double-counting."
    )


def execute(runner: Runner, statements: Sequence[Statement]) -> list[pandas.DataFrame]:
    """Run an ordered list of statements in sequence, returning one frame each.

    Stops at the first exception and lets it propagate. There is no retry here and there
    never will be: the scheduler owns retries, and the reason writes are INSERT OVERWRITE
    into a dated Partition is precisely so that the scheduler's retry converges rather than
    double-counting. A retry loop in this function would be a second, worse scheduler.

    "Lets it propagate" is literal - the same exception object, same type, same traceback,
    so a caller's `except` clause and a test's `pytest.raises` both see exactly what the
    warehouse raised. What this adds is an `Exception.add_note()` entry (3.11+) naming the
    failing statement by index, kind, target, Partition and purpose, plus what already ran.
    A note rides along with the traceback and changes nothing a handler matches on, which is
    why the reporting is done that way rather than by wrapping.

    The frames of the statements that already succeeded are dropped on failure. That is not
    an oversight worth fixing: they are not the answer to anything on their own, and the
    plan is designed to be re-run whole.
    """
    _require_runner(runner, called="execute")
    total = len(statements)
    frames: list[pandas.DataFrame] = []
    for index, statement in enumerate(statements):
        try:
            result = runner.run(statement.sql)
        except Exception as failure:
            note = [_describe(statement, index=index, total=total)]
            context = _already_ran(statements, index=index)
            if context is not None:
                note.append(context)
            failure.add_note("\n".join(note))
            raise
        _require_frame(result, what=_headline(statement, index=index, total=total))
        frames.append(result)
    return frames


def execute_plan(runner: Runner, plan: StatementPlan) -> list[pandas.DataFrame]:
    """`execute` over a StatementPlan's statements, in the plan's dependency order.

    Reads `plan.statements` rather than iterating the plan. The field IS the dependency
    order - `write.plan()` topologically sorts into it - and `StatementPlan.__iter__` is
    documented to yield exactly it, so the two are the same list; taking the field keeps
    this module from depending on a dunder for something a named field already says.
    """
    _require_runner(runner, called="execute_plan")
    return execute(runner, plan.statements)


def frame(runner: Runner, compiled: Compiled) -> pandas.DataFrame:
    """Run one compiled Case and return its rows, with the Case's output names as columns.

    Renames the frame's columns to `compiled.plan.output_names` rather than trusting what
    the warehouse labelled them, so a Case's Lineage node names and its DataFrame column
    names are the same strings. The rename is POSITIONAL, which is safe for exactly one
    reason: `output_names` is also the SELECT order that `compile.build` emitted, so column
    i of the result is output name i by construction.

    That reason is load-bearing enough to be checked. A result whose width is not
    `len(output_names)` did not come from this statement - or the Runner added a column of
    its own - and renaming it positionally would label real numbers with the wrong names,
    which is the failure mode this library exists to refuse. So it raises `ValueError`
    instead. The one exception is a frame with no columns AND no rows, which is what a
    well-behaved Runner returns for a statement that yields nothing; it is passed through
    untouched.
    """
    _require_runner(runner, called="frame")
    result = runner.run(compiled.sql)
    _require_frame(result, what=f"the statement compiled for Case {compiled.name!r}")

    names = tuple(compiled.plan.output_names)
    width = len(result.columns)
    if width == 0 and len(result.index) == 0:
        return result
    if width != len(names):
        raise ValueError(
            f"Case {compiled.name!r} declares {len(names)} output columns "
            f"({', '.join(names)}) but the Runner returned {width}. Refusing to rename "
            "positionally: the result would carry real numbers under the wrong names."
        )
    return result.set_axis(list(names), axis="columns")
