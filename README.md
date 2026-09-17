# SQL Composer

Assembles Hive SQL for closely-related business questions from declared, reusable parts, so
that adding a new question costs only its difference from the existing ones - and emits a
column-level record of where every output number came from.

It never executes anything. `compile_case()` returns a SQL string and a Lineage graph; what
runs them is yours.

The point is not that it writes SQL for you. The point is that it **refuses** to write SQL
it cannot prove. Four mistakes that otherwise produce a query that runs, returns rows, and
is wrong - a re-grain a Metric cannot survive, a join that multiplies the rows a Metric is
measured over, an ambiguous Join path between two tables, a column no Declaration carries - are
build-time refusals with a named remedy. There is no warning class anywhere in the library,
on purpose.

`CONTEXT.md` is the glossary and its terms are the vocabulary of the code.
`docs/adr/0001-sqlglot-over-sqlalchemy.md` is why sqlglot. `docs/design/INTERFACES.md` is
every public signature in one place.

---

## Five nouns

| Noun | What it is |
|---|---|
| **Source** | A physical table the composer may read or write. A Source **is** its Declaration: columns, types, partitioning, joins. Nothing absent from it can be referenced. |
| **Metric** | A named aggregate quantity, declared against the one Source it measures, carrying the rule for whether and how it can be recomputed at a coarser Grain. |
| **Dimension** | A column a Case reports its Metrics across, optionally time-bucketed. |
| **Filter** | A named predicate. The same type narrows a whole Case (a `WHERE`) or scopes one Metric (a conditional aggregate). |
| **Grain** | The level a Case's rows are reported at - its Dimensions, time bucketing included. |

A **Case** is one named business question: a Metric family, a Grain, some Filters. A
**Tag** is how a Case names that family instead of listing it - which is what makes a newly
declared Metric join every Case that asks for the family, with no Case edited.

Everything else the library has is machinery for keeping those six honest: Cardinality and
Fan-out, Join path, Partition, Drift, Lineage, Manifest, Re-aggregation rule. Plus exactly
one concept the glossary does not carry, `Registry`, because a Tag family has to be
resolvable and nothing else owns that lookup.

---

## A Case, end to end

```python
from declarations import REGISTRY
from sqlcomposer import compile_case, lineage
import datetime

compiled = compile_case(REGISTRY, REGISTRY.case("accountable_by_day"),
                        run_date=datetime.date(2026, 9, 17))
print(compiled.sql)
print(lineage.to_text(compiled.lineage))
```

`python tools/smoke.py` runs that and rather more: a write plan, a Lineage traced through a
written table back to its true upstream Sources, and each refusal triggered on purpose so
you can read the messages. Everything it prints comes from the **invented fixture** in
`declarations/` - see the limitations below.

---

## Adding a Case

A Case is usually not a new question; it is the first question cut a different way. Write it
as its difference:

```python
ACCOUNTABLE_BY_WEEK = ACCOUNTABLE_BY_DAY.variant(
    "accountable_by_week",
    grain=Grain.of(BY_WEEK, BY_CARRIER),
)
```

Everything not named is inherited, so the diff in review is the business difference and
nothing else. Three things to know before you rely on it:

* **`writes_to` is not inherited.** It defaults to `None`, never to the parent's target.
  Two Cases writing one Partition would overwrite each other every run.
* **Coarsening the Grain is what trips the Re-aggregation check** across the whole resolved
  Metric family. The cheapest edit is also the checked one - that is the design, not a
  side effect.
* **The parent becomes load-bearing.** Editing it changes every variant's SQL from a line
  that does not mention them. The git-tracked static Lineage artifact is the only defence,
  and regenerating it belongs in CI.

A Case from scratch:

```python
FAILURES_BY_SITE_AND_SEGMENT = Case(
    name="failures_by_site_and_segment",
    metrics=by_tag(ACCOUNTABLE),                       # a family, not a list
    grain=Grain.of(BY_DAY, BY_DESTINATION_SITE, BY_SEGMENT),
    filters=(LAST_7_DAYS,),
    via=("delivery_customer", "delivery_destination_site"),
)
```

`via=` pins **Join names**, not table names, and you only write it after the composer has
refused an ambiguous Join path - it prints the candidates in exactly the form this field takes,
ready to paste, trailing comma and all. It is matched as a **set**: reordering the names
inside it cannot change the statement. When the Case's Metrics measure more than one Source,
which end of the Join path the `FROM` clause names is a second question a set cannot answer, and
`anchor="db.table"` answers it; the refusal prints one candidate per `(anchor, via)` pair.

Note what is *not* in `filters=` there. The question is about failures, but the ACCOUNTABLE
family already contains `failed_deliveries`, which is scoped by `FAILURE_TO_DELIVER`.
Narrowing the Case by that same Filter would make the Metric's conditional aggregate a
tautology - `failed_deliveries` would equal `delivery_attempts` and `failure_rate` would read
`1.0` on every row - so `ScopeCollision` refuses it. The scoping belongs on the Metric, where
the denominator stays honest.

Prefer `by_tag()` over `by_name()`: a Case built by name does not scale horizontally, because
a newly declared Metric will never join it.

## Adding a Source

Generate the Declaration from the warehouse, commit it, then hand-annotate the facts a
`DESCRIBE` cannot report. The generator takes the columns rather than fetching them - the
core connects to nothing, here as everywhere - so you inject the same kind of `describe`
callable the Drift check takes:

```bash
python tools/generate_declarations.py     # prints a draft for an invented table
```

```python
from tools.generate_declarations import write_declaration
write_declaration("mart", "deliveries", describe, Path("declarations/deliveries.py"))
```

It writes every fact a DESCRIBE reports and marks every fact it cannot as a TODO, and it
refuses to overwrite an existing file: the hand annotations are the load-bearing half, and
regenerating over them would delete every Cardinality in it. That is also what
`BreakingDrift`'s remedy means by "re-apply its hand annotations".

```python
DELIVERIES = Source(
    db="mart", table="deliveries",
    one_row_per="delivery attempt",            # prose; the line a reviewer checks against
    columns=(
        Column("delivery_id", "STRING", nullable=False),
        Column("carrier_id", "STRING", nullable=False),
        Column("dt", "STRING", partition=True, nullable=False, note="yyyy-MM-dd"),
        Column("fee_amount", "DECIMAL(18,2)", nullable=False),
    ),
    joins=(
        Join(to="mart.sites",
             keys=(("destination_site_id", "site_id"),),
             cardinality=Cardinality.MANY_TO_ONE,      # this is what detects Fan-out
             name="delivery_destination_site"),        # name it when two edges share a pair
    ),
)
```

* **`cardinality` is the whole of Fan-out detection.** Nothing else knows it and no
  `DESCRIBE` can check it. `one_row_per` exists so a reviewer has one line to check it
  against.
* **`partition=True` changes how values render.** A predicate on a Partition column emits a
  bare literal, because `exp.convert(date(...))` produces `CAST('2026-01-02' AS DATE)` and
  that CAST inside a partition predicate defeats pruning.
* **`name=` the Join** the moment a second edge connects the same pair. Otherwise the
  Registry names it `db.left->db.right`, and a `via=` cannot distinguish two of them.
* **Declare at module level.** The Registry scans module globals; an object built inside a
  function or bound to a private name is never seen.

Then import the module in `declarations/__init__.py` and add it to `Registry.from_modules`.
`freeze()` is called there, once, and is where every cross-Declaration check runs.

For a Source this library writes, set `written_by="<case name>"` and leave `grain` unset -
a written table's Grain comes from the Case that produces it. Its non-Partition columns
must equal that Case's `output_names` **in order**, because Hive matches INSERT columns by
position.

---

## Running the gates

```bash
python tools/smoke.py     # compiles, writes, and fires every refusal; exits non-zero if one doesn't
python -m pytest          # the suite, including the sqlglot escaping matrix
python -m ruff check .    # lint
```

**Regenerate the static Lineage artifact** and diff it. This is the git-tracked output that
makes `variant()`'s action at a distance and late Tag binding reviewable - it is derivable
from the Case definitions with nothing running, and regenerating it in CI is also a check
that every declared Case still compiles:

```bash
python -c "from declarations import REGISTRY; from sqlcomposer import lineage; \
           lineage.write_static_lineage(REGISTRY, 'docs/lineage'); \
           lineage.write_manifests(REGISTRY, 'docs/lineage/manifests')"
git diff --exit-code docs/lineage
```

Two artifacts, both git-tracked and both derived from the Declarations with nothing running.
The Lineage text for a Case that reads a written Source carries **two trees**: what the
statement literally reads, which stops at the written table, and the same tree traced through
that table's Manifest to the Sources the numbers actually came from. The Manifests are
written beside it as JSON, so a reader in another process can trace through a written table
without re-deriving it - `Manifest.from_json` is the other end of that.

**Check for Drift** against the real warehouse. The core connects to nothing, so you inject
the read:

```python
from sqlcomposer import verify

def describe(source):                       # your DESCRIBE FORMATTED, parsed
    return [verify.WarehouseColumn(name=..., type=..., partition=..., nullable=...)]

report = verify.verify(REGISTRY, describe)
print(report.to_text())
report.raise_if_breaking()                  # a separate decision from reporting
```

The check is **scoped** - only columns some Case actually references can break a build -
and **classified**: an added column is informational, a dropped or retyped column a Case
reads is a build-breaker.

**Escalate sqlglot's silence** once at any application entry point:

```python
from sqlcomposer import escalate_sqlglot_logging
escalate_sqlglot_logging()
```

sqlglot degrades by logging rather than raising in several places, and a degradation nobody
reads is indistinguishable from success.

---

## Limitations, honestly

### Four assumptions that were recorded, not supplied

These were not facts anyone gave us. They are load-bearing and they are written down here so
that the day one turns out to be false, the blast radius is visible rather than discovered:

1. **The external query API takes one finished SQL string, not `(sql, params)`.** Everything
   about the rendering discipline follows from it: values enter the tree as escaped literals
   because there is nowhere else for them to go. `Runner.run(sql)` has no `params`
   argument, deliberately - growing one would deepen this dependency without anyone
   deciding to.
2. **The scheduler does not itself substitute values into SQL text.** If it does, every
   guarantee about escaping ends at the moment this library hands the string over.
3. **"Failure to deliver" is a Filter over a shared delivery Source, not a Metric.** The
   fixture declares it that way (`FAILURE_TO_DELIVER`). If it is really several different
   conditions on several Sources, that shape is wrong and the Cases built on it are wrong
   with it.
4. **Contributors want loud build-time refusals regardless of who they are.** There is no
   permissive mode, no `--force`, no warning level. A team that disagrees will route around
   the library rather than configure it.

### The example Declarations are invented

`declarations/deliveries.py` is a **fixture**. Every table, column, type, Cardinality and
business rule in it was made up to exercise the library. The user was asked for a real table
to declare against, declined, and asked for the library to be built anyway. Nothing in it
describes anyone's warehouse.

### Where a wrong number can still get through

* **A mis-annotated Cardinality.** Fan-out detection is exactly as good as the hand
  annotation. A Join marked `MANY_TO_ONE` that the warehouse has quietly made
  `ONE_TO_MANY` inflates every Metric across it, silently, and a `DESCRIBE` cannot catch
  it. `one_row_per` is the only defence and it is prose.
* **A Source with neither `grain` nor `written_by` is treated as atomic.** That silently
  disables the whole re-grain check for it. It is the one permissive default in the design,
  and it is why declaring `grain` on a Source some other pipeline has already coarsened
  matters.
* **Stored rules on a table this library does not write.** `Registry.metric_behind` closes
  the "summed a stored rate" hole for Sources with a `written_by`, and can say nothing
  about a Source coarsened elsewhere.
* **An inner Join keyed on a nullable column.** Hive drops rows on *both* sides of it, which
  deflates every Metric that reaches across the join, and the composer emits that SQL: a
  generated Declaration reports almost everything nullable, so refusing here would block
  every first draft and the only escape (`kind="left"`) changes the semantics rather than
  documenting them. `Registry.nullable_join_keys()` is the list to walk while annotating -
  `tools/smoke.py` prints it next to the write plan - and `nullable=False` is the fix.
* **Drift scope excludes Join keys.** A Case reaches a Join key whenever its path is
  walked, but `Case.referenced_columns` does not include them, so a dropped key column is
  reported as drift and classified informational.
* **`getattr(source, "typo", default)` returns the default.** `UndeclaredColumn` is also an
  `AttributeError` so that `copy`, `pickle` and REPL completion keep working. Anywhere the
  refusal matters, use `Source.column(name)`, which refuses unconditionally.
* **A Metric declared at function scope, or under a private name, is invisible** to the
  Registry's module scan. `EmptyTagFamily` catches a Tag that matches *nothing*; a family
  that is merely missing one of five members raises nothing.
* **A column whose name collides with a `Source` field** (`db`, `table`, `columns`,
  `joins`, `grain`, `note`) is shadowed by normal attribute lookup and must be read with
  `Source.column("name")`.

### What the library cannot express

By omission, and each omission is a decision:

* **No `AVG`, and no `average_of()`.** A mean is `ratio(name, sum_of(...), count_of(...))`,
  which forces you to name a denominator - and naming it is exactly what makes the quantity
  re-derivable at any coarser Grain. An average of averages has no spelling here.
* **No percentiles, stddev, `collect_set`, `approx_count_distinct`, or window functions.**
  An arbitrary aggregate makes the re-grain question undecidable. The first Case needing a
  median forces a new `Aggregate` member plus its provably-correct rule, not a workaround.
* **No `ORDER BY`, no `LIMIT`.** Unsettled scope. The fix would be a field on `Case`, never
  string manipulation on the result.
* **No table aliases and therefore no self-joins.** The Registry refuses two Sources sharing
  a bare table name, which is what makes every column node in the library resolvable without
  one.
* **No column-to-column predicates.** A `Filter` compares a column to a value. A comparison
  between two columns belongs in a `Join`, where a Cardinality can be declared for it, or in
  a warehouse-computed flag column.
* **No raw SQL, anywhere.** There is no `Predicate.from_sql` and there never will be:
  sqlglot escapes string-literal nodes and nothing else, so a predicate parsed from text
  bypasses the entire guarantee.

### The dependency

sqlglot is pinned **exactly**. It is deliberately not semver, and this library leans on
behaviour its documentation does not contract: Hive string-literal escaping, `qualify()`
raising on an unknown column, and `ErrorLevel.RAISE` refusing an untranslatable construct.
`tests/test_escaping.py` carries an escaping matrix of its own so an upgrade that changes
any of it fails here rather than in production.
