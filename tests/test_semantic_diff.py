"""Refactor-safety net: two spellings of one Case must mean the same statement.

The library's promise is that adding a question costs only its difference from the others.
That promise is worth something only if the *non*-differences are provably free: renaming
a Filter, rewriting a Case as a `variant()` of its neighbour, pinning the Join path that
have been inferred anyway, swapping a hand-listed Metric family for the Tag that selects
it - none of those may move a number. String comparison cannot say that, because it also
fails on changes that mean nothing.

`tests/test_compile_golden.py` holds the byte-exact snapshots and answers "did the emitted
text change". This file answers the different question "did the meaning change", between
two Cases that are spelled differently on purpose. Neither subsumes the other: a golden
cannot compare two spellings that were never both snapshotted, and a tree diff cannot
notice a formatting change nobody reviewed.

The other half is the mirror. A change that IS a business difference - a different Filter,
a different Grain, a Metric dropped from the family - must show up. A safety net that
reports "no change" for everything is worse than none, so the identity tests here have
counterparts that prove the same comparison can fail, and a canary that proves
`sqlglot.diff` can see the one difference this file most depends on it seeing.

Three rules, all learned against the pinned sqlglot 30.18.0 and all load-bearing:

* **Never assert on edit order.** `sqlglot.diff`'s matching is heuristic and its edit list
  comes back in an order that varies between runs. Everything here asserts on the
  *presence* and *kind* of edits and on the set of nodes they name, never on position.
* **Never diff a library-built tree against a re-parse of its own SQL.** The Hive parser
  normalises `DATE_FORMAT(dt, 'yyyy-MM-dd')` into a typed `TimeToStr(TimeStrToTime(...))`
  pair, while `grain.py` builds it as an `exp.Anonymous`. The round trip is text-stable and
  tree-*unstable*: `ast.sql()` reproduces the SQL exactly, but `parse_one(sql)` is a
  different tree and diffs against roughly twenty spurious edits. Compare library trees to
  library trees, or parsed trees to parsed trees - never one to the other.
* **`delta_only=True`.** Without it every unchanged node comes back as a `Keep` edit, and
  "no semantic change" would have to be spelled "every edit is a Keep" - the same claim
  with more ways to get it wrong.

`Compiled.ast` is the *qualified* tree, the one `sql` was generated from. That is the
premise every test here rests on, and it is checked first.
"""
from __future__ import annotations

import datetime

import sqlglot
from sqlglot import exp

from declarations import deliveries as fixture
from sqlcomposer import model as m
from sqlcomposer import write
from sqlcomposer.compile import DIALECT, compile_case
from sqlcomposer.declaration import Registry, RunDate

# The Grain every ad-hoc Case below reports at. A constant so that both halves of a
# comparison share a Join path: `BY_CARRIER` is what pulls `mart.carriers` in, and a test
# that dropped it from one side would be diffing a join change as well as whatever it meant
# to diff.
BY_DAY_AND_CARRIER = m.Grain.of(fixture.BY_DAY, fixture.BY_CARRIER)


# ======================================================================================
# Helpers. None of them may depend on edit order.
# ======================================================================================


def _delta(left: exp.Expr, right: exp.Expr) -> tuple[object, ...]:
    """The non-`Keep` edits turning `left` into `right`; empty means no semantic change."""
    return tuple(sqlglot.diff(left, right, delta_only=True))


def _nodes(edit: object) -> tuple[exp.Expr, ...]:
    """Every AST node an edit names: `expression` for Insert/Remove, `source` and `target`
    for Move/Update.

    Reading all three attributes rather than switching on the edit class keeps this working
    if sqlglot grows a fourth kind - and an edit kind this file silently ignored would make
    every "nothing else was touched" assertion below weaker than it reads.
    """
    found = []
    for attribute in ("expression", "source", "target"):
        node = getattr(edit, attribute, None)
        if isinstance(node, exp.Expr):
            found.append(node)
    return tuple(found)


def _touched(edits: tuple[object, ...]) -> frozenset[str]:
    """The SQL text of every node the edits name, as a set - so questions like "did the
    change reach the aggregates?" are answerable without caring about order."""
    return frozenset(node.sql(dialect=DIALECT) for edit in edits for node in _nodes(edit))


def _describe(edits: tuple[object, ...]) -> tuple[str, ...]:
    """A short, ORDER-STABLE rendering of an edit list, for assertion messages.

    Sorted, truncated and de-duplicated on purpose: an unsorted dump would make a failure
    message differ between runs even when the failure did not, and the full `repr` of one
    `Move` over a SELECT is several kilobytes of tree.
    """
    lines = {
        f"{type(edit).__name__}: {node.sql(dialect=DIALECT)[:70]}"
        for edit in edits
        for node in _nodes(edit)
    }
    return tuple(sorted(lines))


def _ast(registry: Registry, case: m.Case, run_date: datetime.date) -> exp.Expr:
    """The qualified tree for a Case. Never re-parsed - see this module's docstring."""
    return compile_case(registry, case, run_date=run_date).ast


def _group_by(ast: exp.Expr) -> str:
    """The GROUP BY clause as text, or "" when there is none.

    Read off the tree rather than rebuilt with `grain.group_by`, which would be the library
    agreeing with itself. What a row of a Case IS - its Grain - is the GROUP BY and nothing
    else; an alias can say anything.
    """
    grouping = ast.args.get("group")
    return "" if grouping is None else grouping.sql(dialect=DIALECT)


def _assert_same(left: exp.Expr, right: exp.Expr, what: str) -> None:
    edits = _delta(left, right)
    assert edits == (), f"{what} changed the statement: {_describe(edits)}"


def _single_metric_case(name: str, **overrides: object) -> m.Case:
    """One Metric, one Grain, two Filters - small enough that a diff stays readable."""
    fields: dict[str, object] = {
        "name": name,
        "metrics": m.by_name("fees_charged"),
        "grain": BY_DAY_AND_CARRIER,
        "filters": (fixture.LAST_7_DAYS, fixture.FAILURE_TO_DELIVER),
    }
    fields.update(overrides)
    return m.Case(**fields)  # type: ignore[arg-type]


# ======================================================================================
# The premise, and the canary.
#
# Every identity test below is vacuous if `diff` cannot see a difference, or if `ast` is
# not the tree the SQL came from. Both are established before anything is concluded.
# ======================================================================================


def test_compiled_ast_is_the_tree_its_sql_came_from(
    registry: Registry, run_date: datetime.date
) -> None:
    """`Compiled.ast` must regenerate `Compiled.sql` exactly, for every declared Case.

    This is what licenses every other test here to diff `ast` and draw a conclusion about
    the emitted SQL. It breaks the day someone keeps the pre-gate tree instead of the
    qualified one - at which point this file would be comparing trees that no longer
    correspond to anything that runs, and would keep passing while it did so.
    """
    for case in registry.cases():
        compiled = compile_case(registry, case, run_date=run_date)
        assert compiled.ast.sql(dialect=DIALECT) == compiled.sql, case.name


def test_diff_sees_a_reordered_projection() -> None:
    """A SELECT list in a different order must come back as a `Move`, not as no change.

    The canary for every `assert _delta(...) == ()` below, and specifically what allows
    `test_the_write_path_embeds_the_read_path_select_unchanged` to conclude anything: Hive
    matches INSERT columns by POSITION, so a reordered projection is a silently wrong write,
    and it is the difference a tree comparison is most likely to wave through.

    Written against hand-parsed text rather than the library, because a canary that used the
    thing under test could not distinguish "diff works" from "the library happens to agree
    with itself".
    """
    first = sqlglot.parse_one("SELECT a AS x, b AS y FROM t", read=DIALECT)
    swapped = sqlglot.parse_one("SELECT b AS y, a AS x FROM t", read=DIALECT)
    edits = _delta(first, swapped)
    assert edits, "sqlglot.diff reported no change for a reordered SELECT list"
    assert any(type(edit).__name__ == "Move" for edit in edits), _describe(edits)


# ======================================================================================
# Identity: different spellings, same statement.
# ======================================================================================


def test_tag_family_and_an_explicit_name_list_compile_to_the_same_statement(
    registry: Registry, run_date: datetime.date
) -> None:
    """`by_tag(ACCOUNTABLE)` must equal `by_name(...)` over the same Metrics - and the
    names are listed in REVERSE so the statement cannot depend on the order they were typed.

    `by_name` is the documented escape hatch from `by_tag`, and the two have to agree or
    switching between them silently moves columns. The reversed argument list is what makes
    this bite: `MetricSelection.resolve` sorts by Metric name for both selections, and a
    change that made the explicit form honour its argument order instead would reorder the
    SELECT list - which is also the INSERT column order, matched by position.

    What it deliberately does NOT claim is that the order is *alphabetical*: both sides are
    resolved by the same code, so a change to the sort key moves both together and is
    invisible here. `tests/test_compile_golden.py` pins the actual order, byte for byte.
    """
    family = registry.tagged(fixture.ACCOUNTABLE)
    assert len(family) > 1, "the fixture's ACCOUNTABLE family must be worth comparing"

    by_tag_case = m.Case(
        name="spelled_by_tag",
        metrics=m.by_tag(fixture.ACCOUNTABLE),
        grain=BY_DAY_AND_CARRIER,
        filters=(fixture.LAST_7_DAYS, fixture.LIVE_CARRIERS),
    )
    reversed_names = tuple(metric.name for metric in reversed(family))
    by_name_case = by_tag_case.variant("spelled_by_name", metrics=m.by_name(*reversed_names))
    _assert_same(
        _ast(registry, by_tag_case, run_date),
        _ast(registry, by_name_case, run_date),
        "naming the family instead of tagging it",
    )


def test_a_variant_and_the_hand_written_case_it_describes_are_the_same(
    registry: Registry, run_date: datetime.date
) -> None:
    """`accountable_by_week` is declared as a one-field `variant()` of the daily Case. The
    same Case written out in full must compile to the same statement.

    This is what makes `variant()` reviewable: the diff in review is the business
    difference, and that is only true if everything unnamed is genuinely inherited. It
    breaks if inheritance drops a Filter, reorders them, or starts inheriting `writes_to` -
    the last of which would point two Cases at one Partition and have them overwrite each
    other on every run.
    """
    inherited = registry.case("accountable_by_week")
    spelled_out = m.Case(
        name="week_written_out",
        metrics=m.by_tag(fixture.ACCOUNTABLE),
        grain=m.Grain.of(fixture.BY_WEEK, fixture.BY_CARRIER),
        filters=(fixture.LAST_7_DAYS, fixture.LIVE_CARRIERS),
    )
    assert inherited.writes_to is None, "variant() must not inherit writes_to"
    _assert_same(
        _ast(registry, inherited, run_date),
        _ast(registry, spelled_out, run_date),
        "rewriting a variant as a full Case",
    )


def test_renaming_a_filter_does_not_reach_the_sql(
    registry: Registry, run_date: datetime.date
) -> None:
    """A Filter's name is documentation. Only its Predicate may reach the statement.

    This breaks the day a name leaks into the SQL - as an alias, a comment, a CTE name - at
    which point renaming a Filter for clarity would show up as a diff in every golden
    statement and in the git-tracked static Lineage, and reviewers would learn to ignore
    both.
    """
    renamed = m.Filter(
        name="a_completely_different_filter_name",
        predicate=fixture.DELIVERIES.dt.between(RunDate() - 6, RunDate()),
    )
    assert renamed.name != fixture.LAST_7_DAYS.name

    original = _single_metric_case(
        "original_filter_names", filters=(fixture.LAST_7_DAYS, fixture.LIVE_CARRIERS)
    )
    renamed_case = original.variant(
        "renamed_filter", filters=(renamed, fixture.LIVE_CARRIERS)
    )
    _assert_same(
        _ast(registry, original, run_date),
        _ast(registry, renamed_case, run_date),
        "renaming a Filter",
    )


def test_two_case_filters_are_the_same_as_one_pre_anded_filter(
    registry: Registry, run_date: datetime.date
) -> None:
    """`filters=(A, B)` must equal `filters=(A & B,)`.

    `compile._filters_predicate` ANDs a Case's Filters in order; `Filter.__and__` builds the
    same conjunction up front. If the two ever disagree - an extra `Paren` that changes
    precedence, a reversed fold, an `OR` typo'd into one of them - a Case would narrow
    differently depending on how its author happened to spell the same restriction, and both
    spellings would still return rows.
    """
    two = _single_metric_case(
        "two_filters", filters=(fixture.LAST_7_DAYS, fixture.LIVE_CARRIERS)
    )
    one = two.variant(
        "one_combined_filter",
        filters=(
            m.Filter(
                name="window_and_live_carriers",
                predicate=fixture.LAST_7_DAYS & fixture.LIVE_CARRIERS,
            ),
        ),
    )
    _assert_same(
        _ast(registry, two, run_date),
        _ast(registry, one, run_date),
        "pre-ANDing two Case Filters into one",
    )


def test_three_spellings_of_one_grain_agree(
    registry: Registry, run_date: datetime.date
) -> None:
    """`Grain.of(...)`, `Grain(dimensions=...)` and a bare tuple on `Case` must all land on
    the same Grain, and therefore on the same projections and the same GROUP BY.

    `Case.__post_init__` normalises the tuple form. This breaks if that normalisation starts
    dropping a time bucket or reordering Dimensions - and Dimension order is SELECT order,
    which is INSERT column order, which is how a written table is read back.
    """
    dimensions = (fixture.BY_DAY, fixture.BY_CARRIER)
    spellings = (m.Grain.of(*dimensions), m.Grain(dimensions=dimensions), dimensions)
    cases = [
        _single_metric_case(f"grain_spelling_{index}", grain=spelling)
        for index, spelling in enumerate(spellings)
    ]
    reference = _ast(registry, cases[0], run_date)
    for case in cases[1:]:
        _assert_same(
            reference, _ast(registry, case, run_date), f"spelling the Grain as {case.name}"
        )


def test_naming_a_metric_already_in_the_tag_family_adds_nothing(
    registry: Registry, run_date: datetime.date
) -> None:
    """`by_tag(F) | by_name(member_of_F)` must not project that Metric twice.

    A duplicated projection is not a crash: it is a second column with the same name and the
    same number. It corrupts a write by position and reads in review as harmless redundancy.
    `MetricSelection.__or__` de-duplicating is the only thing preventing it.
    """
    member = registry.tagged(fixture.ACCOUNTABLE)[0].name
    tagged_only = m.Case(
        name="tagged_only",
        metrics=m.by_tag(fixture.ACCOUNTABLE),
        grain=BY_DAY_AND_CARRIER,
        filters=(fixture.LAST_7_DAYS, fixture.LIVE_CARRIERS),
    )
    union = tagged_only.variant(
        "tagged_plus_a_member",
        metrics=m.by_tag(fixture.ACCOUNTABLE) | m.by_name(member),
    )
    assert union.output_names(registry) == tagged_only.output_names(registry)
    _assert_same(
        _ast(registry, tagged_only, run_date),
        _ast(registry, union, run_date),
        f"naming {member}, which is already in the family",
    )


def test_pinning_the_only_join_path_with_via_changes_nothing(
    registry: Registry, run_date: datetime.date
) -> None:
    """A `via=` that names the Join path the composer would have inferred must be a no-op.

    `via=` exists to break an ambiguity, and the composer prints the candidates in exactly
    the form the field takes so they can be pasted in. That workflow is only safe if pinning
    a path is a tie-break rather than a second code path: if `joins.resolve` built a pinned
    path differently - a different orientation, a different JOIN order, a different ON - then
    pasting the composer's own suggestion could change the numbers of a Case that already
    compiled.
    """
    inferred = registry.case("accountable_by_day")
    join_names = compile_case(registry, inferred, run_date=run_date).plan.join_names
    assert len(join_names) == 1, "this test needs a Case with exactly one declared Join path"

    pinned = inferred.variant("pinned_path", via=join_names)
    _assert_same(
        _ast(registry, inferred, run_date),
        _ast(registry, pinned, run_date),
        f"pinning via={join_names}, the Join path already inferred",
    )


def test_the_write_path_embeds_the_read_path_select_unchanged(
    registry: Registry, run_date: datetime.date
) -> None:
    """The SELECT inside `INSERT OVERWRITE` must be the SELECT `compile_case` emits.

    Two modules assemble it - `write.insert_overwrite` and `compile.compile_case` - and on
    the day they drift the written table holds different numbers than the same Case read
    directly, with nothing to compare them against. `test_compile_golden.py` asserts the
    same thing as a byte-exact `endswith` against a snapshot; this asserts it as a tree
    comparison between two live compilations, so it survives a wholesale regeneration of the
    goldens and still fails if the two paths disagree.

    Column ORDER counts as drift here and is caught: Hive matches INSERT columns by
    position, and a reorder comes back as a `Move` - see `test_diff_sees_a_reordered_
    projection`.

    Both trees are parsed from text so the parser's normalisation applies to both sides;
    diffing a parsed tree against a library-built one is the trap this module's docstring
    describes.
    """
    case = registry.case("accountable_by_day")
    assert case.writes_to is not None, "this test needs a Case that writes"

    statement = write.insert_overwrite(registry, case, run_date=run_date)
    insert = sqlglot.parse_one(statement.sql, read=DIALECT)
    assert isinstance(insert, exp.Insert)
    embedded = insert.expression.copy()
    assert embedded.parent is None, "copy() must detach, or the diff reports a spurious Move"

    read_path = sqlglot.parse_one(
        compile_case(registry, case, run_date=run_date).sql, read=DIALECT
    )
    _assert_same(read_path, embedded, "wrapping the SELECT in INSERT OVERWRITE")


# ======================================================================================
# The mirror: a real change must show up.
#
# Each of these asserts that the diff is non-empty AND that it names the right nodes and
# leaves the rest alone. Asserting only "something changed" would also pass for a diff
# that reported the whole tree, which is the failure mode of a matcher that stopped
# matching.
# ======================================================================================


def test_a_different_filter_shows_up_as_an_edit(
    registry: Registry, run_date: datetime.date
) -> None:
    """Swapping one Case-level Filter for another must appear in the diff, and must touch
    the predicate only.

    Both Filters read `mart.deliveries`, so the Join path, the Grain and the aggregate are
    identical on both sides. Anything the diff names beyond the predicate would mean a
    Filter is reaching somewhere it should not - the specific fear being a Case-level Filter
    that also narrowed an aggregate.
    """
    before = _single_metric_case("filter_before")
    after = _single_metric_case(
        "filter_after", filters=(fixture.LAST_7_DAYS, fixture.DELIVERED_LATE)
    )
    edits = _delta(_ast(registry, before, run_date), _ast(registry, after, run_date))
    touched = _touched(edits)

    assert edits, "a different Filter must show up as a semantic change"
    assert any("failure_reason" in text for text in touched), _describe(edits)
    assert any("late_flag" in text for text in touched), _describe(edits)
    assert not any("fee_amount" in text for text in touched), (
        f"a Filter change must not touch the aggregate: {_describe(edits)}"
    )


def test_a_different_grain_shows_up_as_an_edit(
    registry: Registry, run_date: datetime.date
) -> None:
    """Re-graining from DAY to WEEK must appear in the diff, and must not touch the Metric.

    `variant(grain=...)` is the cheapest edit a contributor can make and the one that
    silently changes every number if the bucket expression stops being rebuilt. The
    aggregate is untouched here because `fees_charged` is a plain SUM over atomic rows -
    a Metric whose re-aggregation depends on the Grain is a re-grain question, and belongs to
    `tests/test_grain.py` rather than here.
    """
    daily = _single_metric_case("grain_daily")
    weekly = _single_metric_case(
        "grain_weekly", grain=m.Grain.of(fixture.BY_WEEK, fixture.BY_CARRIER)
    )
    daily_ast = _ast(registry, daily, run_date)
    weekly_ast = _ast(registry, weekly, run_date)
    edits = _delta(daily_ast, weekly_ast)
    touched = _touched(edits)

    assert edits, "a different Grain must show up as a semantic change"
    assert any("dt_week" in text for text in touched), _describe(edits)
    assert not any("fee_amount" in text for text in touched), (
        f"re-graining a SUM must not rewrite the aggregate: {_describe(edits)}"
    )
    # The alias alone is not the re-grain. A bucket that stopped being rebuilt would still
    # relabel the column `dt_week` and still produce a non-empty diff, while grouping by the
    # day - so the rows would be daily rows wearing a weekly name. Only the GROUP BY says
    # what a row IS.
    assert _group_by(daily_ast) != _group_by(weekly_ast), (
        "re-graining changed the alias but not the GROUP BY: the rows are still daily"
    )


def test_excluding_a_metric_from_the_family_shows_up_as_an_edit(
    registry: Registry, run_date: datetime.date
) -> None:
    """`without(...)` must remove exactly that Metric's projection and nothing else.

    An exclusion is how a Case opts out of one member of a Tag family it otherwise wants. If
    the diff named more than the excluded Metric, the exclusion would be changing the other
    numbers too - and the Case would still compile and still return rows.
    """
    full = registry.case("accountable_by_day")
    trimmed = full.variant(
        "accountable_without_active_couriers",
        metrics=m.by_tag(fixture.ACCOUNTABLE).without(
            "active_couriers", because="proving the exclusion reaches the SQL"
        ),
    )
    assert "active_couriers" in full.output_names(registry)
    assert "active_couriers" not in trimmed.output_names(registry)

    edits = _delta(_ast(registry, full, run_date), _ast(registry, trimmed, run_date))
    touched = _touched(edits)

    assert edits, "dropping a Metric from the family must show up as a semantic change"
    assert any("active_couriers" in text for text in touched), _describe(edits)
    for survivor in ("fee_amount", "failure_reason"):
        assert not any(survivor in text for text in touched), (
            f"excluding one Metric must leave the others alone: {_describe(edits)}"
        )


def test_a_different_run_date_changes_only_literals(
    registry: Registry, run_date: datetime.date
) -> None:
    """A new `run_date` must move the bound literals and nothing structural.

    `RunDate` is the library's only deferred value, and the promise is that it binds into
    literal nodes rather than being formatted into SQL text. If a date ever reached a
    projection, a JOIN or the GROUP BY, the same Case would mean different things on
    different days, and the git-tracked static Lineage would churn once per run - which is
    how a reviewer learns to stop reading it.
    """
    case = registry.case("accountable_by_day")
    other_day = datetime.date(2026, 1, 2)
    assert other_day != run_date

    edits = _delta(
        _ast(registry, case, run_date), _ast(registry, case, other_day)
    )
    touched = _touched(edits)

    assert edits, "a different run_date must show up as a semantic change"
    assert any(other_day.isoformat() in text for text in touched), _describe(edits)
    for structural in ("SUM(", "COUNT(", "DATE_FORMAT", "JOIN", "GROUP BY"):
        assert not any(structural in text for text in touched), (
            f"a run_date must only move literals, but it touched {structural}: "
            f"{_describe(edits)}"
        )
