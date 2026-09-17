"""End-to-end smoke run over the fixture Declarations. `python tools/smoke.py`

Not a test - the suite under tests/ owns assertions. This is the thing a human runs to see
the library work: one Case compiled to Hive, its column-level Lineage as a text tree and as
DOT, a write plan with its Partition and its Manifest, and then each of the four refusals of
decision 3 triggered on purpose so the messages can be read rather than trusted.

Everything it prints comes out of the INVENTED FIXTURE in declarations/, which is not
anyone's real schema. See declarations/deliveries.py.

The four refusals, and the mistake each one stands in for:

  FanOut               reporting a Metric measured on the carrier next to a delivery-day
                       Dimension, which counts the carrier once per delivery
  AmbiguousJoinPath    reaching mart.sites without saying whether that means the origin
                       site or the destination site - two Join paths, two different
                       numbers
  UnsafeReAggregation  summing a stored COUNT(DISTINCT) up from days to weeks
  UndeclaredColumn     a misspelled column name

Each of the four otherwise produces SQL that runs and returns a plausible wrong number.
That is the whole reason they are refusals rather than warnings.

A seventh section shows the re-grain refusal arriving by its second door - a Metric
declared against a written Source under a rule that contradicts the one its numbers were
produced by. That is the shape the library did NOT refuse until `Registry.metric_behind`
was wired into `grain.plan_metric`; it is here so a regression is visible rather than
silent.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import Callable

# Run straight from a checkout, with no install step: a smoke script that needs `pip
# install -e .` first is a smoke script nobody runs.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from declarations import REGISTRY  # noqa: E402
from declarations import deliveries as fixture  # noqa: E402
from sqlcomposer import ComposerError, Registry, compile_case, sum_of  # noqa: E402
from sqlcomposer import lineage, write  # noqa: E402
from sqlcomposer.model import Case, Grain, by_name  # noqa: E402

RUN_DATE = datetime.date(2026, 9, 17)
"""Fixed rather than `date.today()`, so two runs of this script produce the same output and
a diff of it means something."""


def heading(text: str) -> None:
    print()
    print("=" * 88)
    print(text)
    print("=" * 88)


def refusal(label: str, build: Callable[[], object]) -> None:
    """Run something that must refuse, and print the refusal it produced.

    Exits non-zero if it does NOT refuse: a smoke script that silently stops proving the
    four refusals is worse than no smoke script, because it still prints six green
    sections above this one.
    """
    print()
    print(f"--- {label} " + "-" * max(0, 84 - len(label)))
    try:
        build()
    except ComposerError as refused:
        print(refused)
        return
    print(f"!! {label}: NO REFUSAL. This is a bug in the library, not in the fixture.")
    sys.exit(1)


def main() -> int:
    case = fixture.ACCOUNTABLE_BY_DAY

    heading(f"1. Hive SQL for Case {case.name!r} at {case.grain}")
    compiled = compile_case(REGISTRY, case, run_date=RUN_DATE)
    print(compiled.sql)

    heading(f"2. Lineage for {case.name!r} - builder-derived, column-level")
    print(lineage.to_text(compiled.lineage))

    heading("3. The same Lineage as DOT (a string; there is no graphviz dependency)")
    dot = lineage.to_dot(compiled.lineage, name=case.name)
    print("\n".join(dot.splitlines()[:12]))
    print(f"... {len(dot.splitlines()) - 13} more lines, then }}")

    heading("4. Write plan: two Cases, ordered by dependency")
    # accountable_by_day writes mart.delivery_health_daily; weekly_health_from_daily reads
    # it. The plan is passed in the wrong order on purpose - write.plan sorts it.
    plan = write.plan(
        REGISTRY,
        [fixture.WEEKLY_HEALTH_FROM_DAILY, fixture.ACCOUNTABLE_BY_DAY],
        run_date=RUN_DATE,
    )
    for index, statement in enumerate(plan, start=1):
        print()
        print(f"[{index}/{len(plan)}] {statement.kind.value}  target={statement.target}")
        print(f"      {statement.purpose}")
        if statement.partition:
            rendered = ", ".join(f"{name} = {text}" for name, text in statement.partition)
            print(f"      a retry replaces exactly: PARTITION({rendered})")
        print(f"      {statement.sql}")
    print()
    print(f"manifests emitted: {', '.join(m.source for m in plan.manifests) or '(none)'}")
    print()
    # Printed beside the write because this is the report nothing refuses on, and a report
    # nothing prints is a report nobody reads. An inner Join keyed on a column still
    # declared nullable drops rows on BOTH sides and deflates every Metric that reaches
    # across it - and unlike the four refusals below, the composer emits that SQL. The
    # remedy is the hand annotation `nullable=False` on the Declaration, once the warehouse
    # has been checked; the empty list below is what a fully annotated fixture looks like.
    untightened = REGISTRY.nullable_join_keys()
    print("inner Join keys still declared nullable (a report, never a refusal):")
    for join_name, ref in untightened:
        print(f"      {join_name}: {ref.qualified}")
    if not untightened:
        print("      (none - every declared inner Join key is annotated nullable=False)")

    heading("5. Tracing through the written table to the true upstream Sources")
    weekly = compile_case(REGISTRY, fixture.WEEKLY_HEALTH_FROM_DAILY, run_date=RUN_DATE)
    traced = lineage.trace_through(weekly.lineage, plan.manifests)
    print(lineage.to_text(traced, "weekly_failure_rate"))

    heading("6. The four refusals of decision 3, triggered on purpose")

    refusal(
        "FanOut - a carrier Metric reported by delivery day",
        lambda: compile_case(
            REGISTRY,
            Case(
                name="fleet_size_by_delivery_day",
                metrics=by_name(fixture.CARRIER_FLEET_SIZE),
                grain=Grain.of(fixture.BY_DAY),
            ),
            run_date=RUN_DATE,
        ),
    )

    refusal(
        "AmbiguousJoinPath - origin site or destination site?",
        lambda: compile_case(
            REGISTRY,
            Case(
                name="attempts_by_site",
                metrics=by_name(fixture.DELIVERY_ATTEMPTS),
                grain=Grain.of(fixture.BY_DAY, fixture.BY_DESTINATION_SITE),
            ),
            run_date=RUN_DATE,
        ),
    )

    refusal(
        "UnsafeReAggregation - a stored COUNT(DISTINCT) rolled up to weeks",
        lambda: compile_case(
            REGISTRY,
            Case(
                name="active_couriers_by_week",
                metrics=by_name(fixture.STORED_ACTIVE_COURIERS),
                grain=Grain.of(fixture.WRITTEN_BY_WEEK, fixture.WRITTEN_BY_CARRIER),
            ),
            run_date=RUN_DATE,
        ),
    )

    refusal(
        "UndeclaredColumn - a misspelled column, at import time",
        lambda: fixture.DELIVERIES.column("fee_amonut"),
    )

    heading("7. The same re-grain refusal arriving by the other door")
    print(
        "A Metric declared against a WRITTEN Source is a fresh Declaration and can claim\n"
        "any Re-aggregation rule it likes about numbers it did not produce. Both of these\n"
        "are well-formed SUMs of well-typed columns; both are wrong. The Metric that wrote\n"
        "the column is what knows so, and Registry.metric_behind is the hop that asks it.\n"
        "\n"
        "Built against a Registry assembled here rather than declarations/REGISTRY - every\n"
        "entry point takes its Registry as the first argument, so nothing is a global."
    )
    probe = Registry.from_modules(fixture, name="smoke-probe").add(
        sum_of("weekly_couriers_summed", fixture.DELIVERY_HEALTH_DAILY.active_couriers),
        sum_of("weekly_rate_summed", fixture.DELIVERY_HEALTH_DAILY.failure_rate),
    ).freeze()
    for name in ("weekly_couriers_summed", "weekly_rate_summed"):
        refusal(
            f"UnsafeReAggregation - {name}",
            lambda name=name: compile_case(
                probe,
                Case(
                    name=f"naive_{name}",
                    metrics=by_name(name),
                    grain=Grain.of(fixture.WRITTEN_BY_WEEK, fixture.WRITTEN_BY_CARRIER),
                ),
                run_date=RUN_DATE,
            ),
        )

    print()
    print("=" * 88)
    print("All seven sections produced output and every refusal fired.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
