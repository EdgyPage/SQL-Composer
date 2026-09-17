# Interfaces

Every public signature in `sqlcomposer`, in one place. This is the contract seven agents
implement against simultaneously without talking to each other, so anything ambiguous here
becomes a difference in behaviour at merge time.

All ten modules are now **implemented**, by seven agents working in parallel against this
page. It remains the contract: a signature here is frozen, and the source file carries the
detail. Where the two disagree, the source file wins and this page is the thing to fix.
Two entries below were amended after the reconciliation pass, and both say so where they
appear: `Registry.native_grain`'s aliasing, and the stored-rule check `grain.plan_metric`
runs on top of `check_regrain`.

---

## Conventions that hold everywhere

| Rule | Detail |
|---|---|
| **Registry first** | Every function that needs the Registry takes it as its first positional argument. `CasePlan` does not hold one. |
| **Frozen everywhere** | Every value object is a frozen dataclass. Nothing in the library mutates one after construction. |
| **Node identity** | A column is `db.table.column` (`ColumnRef.qualified`) in the SQL, the Lineage graph, the DOT export, the drift report and every refusal message. Nothing re-derives it. |
| **Table aliases** | There are none. `Registry.add` refuses two Sources sharing a bare table name, so every column node is qualified by the bare table name and `qualify()` supplies `AS \`table\`` itself. |
| **Literal discipline** | A Python value reaches the AST only through `Column.literal` / `ColumnRef.literal`. No f-string, no `.format`, no `maybe_parse` of interpolated text - anywhere. |
| **Generation** | One `.sql()` call in the library, in `compile.render`, always with `unsupported_level=sqlglot.ErrorLevel.RAISE`, always inside `errors.warnings_are_refusals()`. |
| **Ordering** | Metrics sort by name; Dimensions keep Grain order; `Case.output_names` is Dimensions-then-Metrics and is simultaneously the Lineage node set, the SELECT order and the INSERT column order. |
| **Deferred values** | `RunDate` is the only one. A Predicate holding one raises `UnboundRunDate` unless `run_date: datetime.date` is supplied at compile time. |
| **Refusals** | Everything in `errors.py` is a refusal. There is no warning class, on purpose. |

### sqlglot facts verified against the pinned 30.18.0

* `exp.Expr` is the AST base; `exp.Expression` subclasses it.
* `exp.Column` has `eq/neq/isin/is_/between/like` but **not** `gt/lt/gte/lte` - build
  `exp.GT(this=..., expression=...)`, `exp.LTE(...)` etc. `ColumnRef` already hides this.
* `exp.Count(this=col, distinct=True)` does **not** emit DISTINCT. Use
  `exp.Count(this=exp.Distinct(expressions=[col]))`.
* `exp.func("trunc", col, "MM").sql(dialect="hive", unsupported_level=RAISE)` **raises**.
  Hive-only functions must be `exp.Anonymous(this="date_format", expressions=[...])`.
* `exp.DataType.build("NOPE", dialect="hive")` raises `ParseError` - `Column` uses this for
  free import-time type validation.
* `exp.convert(date(2026,1,2))` renders `CAST('2026-01-02' AS DATE)`, which defeats Hive
  partition pruning inside a PARTITION predicate. `Column.literal` emits a bare literal on
  a Partition column for exactly this reason.
* `exp.and_` / `exp.or_` parenthesise correctly by precedence; `exp.not_` parenthesises.
* Hive string escaping: a backslash becomes two, then a quote becomes backslash-quote -
  backslash-first, so an injected sequence cannot break out of a literal.
* `qualify(ast, schema=..., dialect="hive")` raises `OptimizeError` on an unknown column and
  rewrites to `` SELECT `t`.`a` AS `a` FROM `d`.`t` AS `t` ``. Golden SQL is written against
  that qualified form. Star expansion **silently no-ops** on an incomplete schema, so the
  gate always runs against `Registry.schema()` entire.
* `sqlglot.diff` match ordering varies between runs. Never assert on edit order.

---

## `sqlcomposer/errors.py` — the refusal hierarchy

```
ComposerError(subject: str, problem: str, remedy: str, **context)   # keyword-only
├── DeclarationError            the Declarations are wrong (import time)
│   ├── UndeclaredColumn(source, column, did_you_mean=())           # also AttributeError
│   ├── UndeclaredSource(qualified, known=())
│   ├── UnknownMetric(metric, known=())
│   ├── UnknownFilter(filter, known=())
│   ├── UnknownCase(case, known=())
│   ├── UnknownJoin(case, join, known=())
│   ├── DuplicateDeclaration(kind, name)
│   ├── InvalidDeclaration(subject, problem, remedy, **context)
│   ├── LiteralTypeMismatch(column, declared_type, value, reason=None)
│   ├── RegistryFrozen(kind, name)
│   └── RegistryNotFrozen(operation)
├── RefusalError                sound Declarations, unsafe Case
│   ├── EmptyTagFamily(tag, known=(), case=None)
│   ├── ScopeCollision(case, filter, metric, outputs=())
│   ├── JoinError
│   │   ├── NoJoinPath(case, anchor, unreachable)
│   │   ├── AmbiguousJoinPath(case, anchor, candidates, anchors=())
│   │   │                                                   # candidates: Seq[Seq[join name]]
│   │   │                                                   # anchors: parallel spines, when
│   │   │                                                   #   the spine is what is ambiguous
│   │   └── FanOut(metric, measures, join, cardinality, path=())
│   ├── ReAggregationError
│   │   ├── UnsafeReAggregation(metric, rule, native, target, stored_by=None, **context)
│   │   ├── GrainTooFine(metric, native, target, offending=())
│   │   └── GrainNotComparable(metric, native, target)
│   ├── UnboundRunDate(subject, text)
│   └── PlanInvariantViolated(case, invariant, detail)
├── RenderError
│   ├── ResolutionFailed(case, sqlglot_message)              # wraps OptimizeError
│   └── UnsupportedConstruct(case, sqlglot_message)          # wraps UnsupportedError
└── DriftError
    └── BreakingDrift(source, dropped=(), retyped=None, used_by=())
```

Every constructor is **keyword-only**. Every error carries `.subject`, `.problem`,
`.remedy` and `.context`, plus its own typed attributes - assert on attributes in tests,
never on prose. `__str__` renders three lines plus sorted context.

```python
@contextlib.contextmanager
def warnings_are_refusals(logger_name: str = "sqlglot") -> Iterator[None]
```
Escalates sqlglot's logger so a logged warning raises `RenderError`.

**Which refusal for which mistake** (decision 3's four, plus their neighbours):

| Mistake | Refusal | Raised by |
|---|---|---|
| column absent from a Declaration | `UndeclaredColumn` | `Source.__getattr__`, `Source.column`, `compile.qualify_gate` (as `ResolutionFailed`) |
| unprovable re-grain | `UnsafeReAggregation` / `GrainTooFine` / `GrainNotComparable` | `grain.check_regrain` |
| re-aggregation whose rule contradicts the Metric that wrote the column | `UnsafeReAggregation(stored_by=...)` | `grain.plan_metric`, via `Registry.metric_behind` |
| Join path fans out a measured Source | `FanOut` | `joins.check_fan_out` |
| more than one Join path | `AmbiguousJoinPath` | `joins.resolve` |
| more than one possible spine | `AmbiguousJoinPath(anchors=...)` | `joins.spine` |
| Tag that matches nothing | `EmptyTagFamily` | `Registry.tagged`, at `freeze()` and at resolve |
| value that cannot inhabit the column type | `LiteralTypeMismatch` | `Column.literal`, eagerly at predicate construction |
| non-finite number, or one whose text is not numeric | `LiteralTypeMismatch(reason=...)` | `Column.accepts`, `Column.literal` |
| Case-level Filter that is also a Metric's scope | `ScopeCollision` | `compile.plan` |

---

## `sqlcomposer/declaration.py` — Declarations

A Source **is** its Declaration; there is no separate Declaration type.

### Type aliases

```python
HiveType = str                         # "STRING", "BIGINT", "DECIMAL(18,2)" verbatim
Value = str|int|float|Decimal|bool|date|datetime|None|RunDate
JoinPath = tuple[JoinStep, ...]        # chain of declared joins, spine-first
```

### Module functions

```python
@functools.lru_cache(maxsize=None)
def hive_type(text: HiveType) -> exp.DataType          # InvalidDeclaration on nonsense
def python_types_for(text: HiveType) -> tuple[type, ...]   # () = no literal comparison
def generate(db: str, table: str, columns: Sequence[verify.WarehouseColumn], *,
             module: bool = True) -> str
```

`generate` is decision 8's first clause - "Declarations are generated from the warehouse" -
in the only form a compile-only library can honour it: it takes the columns, it does not go
and get them. `tools/generate_declarations.py` wraps it with the same kind of injected
`describe` callable `verify.verify` takes. It is the exact mirror of the Drift check, over
the same four per-column facts, and it leaves `joins=()`, `one_row_per=""` and every `note`
as TODOs rather than guessing - a Cardinality nobody checked reads identically to one
somebody did.

### `Cardinality(Enum)`

`ONE_TO_ONE="1:1"`, `MANY_TO_ONE="N:1"`, `ONE_TO_MANY="1:N"`, `MANY_TO_MANY="N:N"`.
Oriented left-to-right as declared.

```python
def inverted(self) -> Cardinality
@property fans_out -> bool            # ONE_TO_MANY, MANY_TO_MANY
@property determines_right -> bool    # MANY_TO_ONE, ONE_TO_ONE
```

### `TimeBucket(Enum)`

`HOUR DAY WEEK MONTH QUARTER YEAR`. **Partial order.** `DAY < WEEK`;
`DAY < MONTH < QUARTER < YEAR`; **WEEK and MONTH are incomparable** (ISO weeks straddle
months). `HOUR` is finest.

```python
def coarsens(self, other: TimeBucket) -> bool    # self is other, or other rolls up into self
def comparable(self, other: TimeBucket) -> bool
```

### `RunDate` *(frozen)*

```python
RunDate(offset_days: int = 0)
def __sub__(self, days: int) -> RunDate
def __add__(self, days: int) -> RunDate
def resolve(self, run_date: date) -> date
```
The only deferred value in the library. `RunDate() - 6` is six days before the run date.

### `Predicate` *(frozen, `eq=False` — compares by identity; compare `.text`)*

```python
Predicate(build: Callable[[date|None], exp.Condition],
          columns: frozenset[ColumnRef], text: str, deferred: bool = False)
def to_sqlglot(self, *, run_date: date | None = None) -> exp.Condition   # UnboundRunDate
@property sources -> frozenset[Source]
__and__ / __or__ (accept Predicate or Filter) -> Predicate ; __invert__ -> Predicate
```
No `from_sql`, ever. `columns` is known without walking an AST: those refs are the Filter's
Lineage edges and the Drift scope.

### `Column` *(frozen)*

```python
Column(name: str, type: HiveType, partition: bool = False,
       nullable: bool = True, note: str = "")
def accepts(self, value: Value) -> bool
def literal(self, value: Value, *, run_date: date|None = None, subject: str = "") -> exp.Expr
def to_sqlglot(self) -> exp.DataType
```
`__post_init__` refuses an empty name, a leading-underscore name, and an unparseable type.

**`literal` rules** — the whole of decision 10 in one method:

| Column | Value | Emits |
|---|---|---|
| any | `None` | `NULL` |
| text type | value from a `RunDate` | `exp.Literal.string("2026-09-17")` |
| text type | a hand-written `date` | `LiteralTypeMismatch` |
| any | int / float / Decimal | `exp.Literal.number`, from text the library formats and validates itself - never `str(value)`, which a subclass controls |
| any | non-finite float / Decimal | `LiteralTypeMismatch(reason=...)` - `NaN` would render as `NULL` (or as the bare token `nan` on a Partition column) |
| Partition, other | anything | `exp.Literal.string` (no CAST) |
| not Partition | anything else | `exp.convert` (CAST where typed) |

### `ColumnRef` *(frozen)* — what attribute access returns

```python
ColumnRef(source: Source, column: Column)
@property qualified -> str        # "db.table.column" = the Lineage node id
@property name / type / partition / nullable
def to_sqlglot(self) -> exp.Column                  # exp.column(name, table=source.table)
def literal(self, value: Value, *, run_date: date|None = None) -> exp.Expr

# predicates — every value is validated EAGERLY at construction
def eq/ne/gt/ge/lt/le(self, value: Value) -> Predicate
def isin(self, *values: Value) -> Predicate         # refuses an empty list
def not_in(self, *values: Value) -> Predicate
def between(self, low: Value, high: Value) -> Predicate
def like(self, pattern: str) -> Predicate
def is_null(self) -> Predicate
def is_not_null(self) -> Predicate
```

### `Join` *(frozen)* — a declared edge, carried by the Source it leaves

```python
Join(to: str,                                    # "db.table"
     keys: tuple[tuple[str, str], ...],          # (left column, right column)
     cardinality: Cardinality,                   # oriented owner -> to
     name: str = "",                             # "" -> "db.left->db.right" at freeze()
     kind: Literal["inner","left"] = "inner",
     note: str = "")
```
Refuses empty keys and an unknown `kind`.

### `JoinStep` *(frozen)* — one oriented traversal; the universal currency

```python
JoinStep(name: str, frm: Source, to: Source,
         keys: tuple[tuple[ColumnRef, ColumnRef], ...],
         cardinality: Cardinality, kind: Literal["inner","left"] = "inner")
def inverted(self) -> JoinStep       # name is INVARIANT under inversion
@property fans_out -> bool
def on(self) -> exp.Condition        # keys ANDed, column nodes on both sides
```

### `Source` *(frozen)*

```python
Source(db: str, table: str, columns: tuple[Column, ...],
       joins: tuple[Join, ...] = (),
       grain: tuple[str, ...] | None = None,          # None = atomic rows
       grain_buckets: tuple[tuple[str, TimeBucket], ...] = (),
       written_by: str | None = None,                 # a Case name
       one_row_per: str = "", note: str = "")

def __getattr__(self, name) -> ColumnRef     # UndeclaredColumn (+ did_you_mean)
def column(self, name: str) -> ColumnRef     # same refusal, unconditional
def has(self, name: str) -> bool
def refs(self) -> tuple[ColumnRef, ...]
@property qualified -> str                   # "db.table"
@property partition_columns -> tuple[Column, ...]      # declaration order
def join_to(self, qualified: str) -> tuple[Join, ...]
def to_sqlglot(self) -> exp.Table
def schema_entry(self) -> dict[str, HiveType]
def __dir__(self) -> list[str]               # completion sees declared columns
```

`grain` and `written_by` are mutually exclusive (refused in `__post_init__`): a Source this
library writes takes its Grain from the producing Case. `grain_buckets` names the bucket of
a bucketed column in `grain`, for a Source another pipeline has already coarsened only.

**Known wrinkle:** a declared column colliding with a field name (`db`, `table`, `columns`,
`joins`, `grain`, `note`, ...) is shadowed by normal attribute lookup and must be read with
`Source.column("name")`. Loud, not silent - the attribute returns a str or a tuple.

**Known cost:** `UndeclaredColumn` is also an `AttributeError`, so `hasattr(src, "typo")`
returns `False` and `getattr(src, "typo", default)` yields the default instead of raising.
Anything that must refuse uses `Source.column`.

### `Registry` — the one added concept

```python
Registry(name: str = "default")
def add(self, *declared: Source|Metric|Filter|Case) -> Registry        # chains
@classmethod from_modules(cls, *modules: ModuleType, name="default") -> Registry
def freeze(self) -> Registry                                            # chains
@property frozen -> bool
def require_frozen(self, operation: str) -> None                        # RegistryNotFrozen

# lookups (all sorted, all refusing)
def source(self, qualified: str) -> Source
def sources(self) -> tuple[Source, ...]
def source_of_table(self, table: str) -> Source
def resolve_column(self, qualified: str) -> ColumnRef       # "db.table.column" -> ref
def metric(self, name: str) -> Metric
def metrics(self) -> tuple[Metric, ...]
def tagged(self, *tags: str, case: str | None = None) -> tuple[Metric, ...]
def tags(self) -> frozenset[str]
def filter(self, name: str) -> Filter
def filters(self) -> tuple[Filter, ...]
def case(self, name: str) -> Case
def cases(self) -> tuple[Case, ...]
def join(self, name: str) -> JoinStep                       # declared orientation
def joins(self) -> tuple[JoinStep, ...]                     # declared orientation
def joins_from(self, source: Source) -> tuple[JoinStep, ...]   # oriented to leave `source`
def nullable_join_keys(self) -> tuple[tuple[str, ColumnRef], ...]

# derived facts
def writing_case(self, source: Source) -> Case | None
def native_grain(self, source: Source) -> Grain | None
def metric_behind(self, ref: ColumnRef) -> Metric | None
def referenced_columns(self) -> frozenset[ColumnRef]

# sqlglot export
def schema_dict(self) -> dict[str, dict[str, dict[str, HiveType]]]
def schema(self) -> MappingSchema                            # ALWAYS the whole schema
```

* `from_modules` scans public module-level globals and does **not** freeze - call
  `.freeze()` yourself once every declarations module is imported.
* `add` refuses two Sources sharing a bare table name (this is what makes alias-free column
  qualification safe) and any duplicate name within a kind.
* `tagged` checks **each Tag individually** - a Tag matching nothing raises `EmptyTagFamily`
  even when the other Tags in the same call matched. That refusal is why `Tag` is `str`.
* `freeze()` resolves join targets, checks join keys exist on both sides, checks join name
  uniqueness, checks the write->read link in BOTH directions (each `written_by` names a Case
  that writes exactly this Source, AND each `Case.writes_to` names a Source that names it
  back), checks every `Case.via` names a real edge and every `Case.anchor` a real Source, and
  checks every Tag a Case uses matches something. The second write direction is not
  symmetry for its own sake: everything downstream reads only the Source's half, so a target
  the composer writes without the backlink has no native Grain and the whole unsafe-re-grain
  refusal is silently disabled for every Metric reading it. It also means two Cases cannot
  both declare `writes_to` one target - only one of them can be named back.
* `native_grain` prefers the writing Case's Grain, **re-pointed at the written Source's own
  columns by output name**; otherwise builds from `grain` + `grain_buckets`; otherwise None.
  Every Dimension it returns is aliased to the column it reads, so the Grain publishes the
  names the written table's own DESCRIBE reports - that string is what every re-grain
  refusal prints as `native=`, and without the alias a stored `dt_day` at DAY would print
  as `dt_day_day`, naming a column nobody can find.
* `metric_behind` matches a written Source's column to the producing Case's Metric **by
  name**, which is why `Case.output_names` must stay stable.

---

## `sqlcomposer/model.py` — the parts of a question

```python
Tag = str     # typo safety comes from Registry.tagged refusing per-Tag, not from a wrapper
```
`Cardinality` and `TimeBucket` are re-exported here.

### `Aggregate(Enum)` — `SUM COUNT COUNT_DISTINCT MIN MAX RATIO`

**There is no AVG and no `average_of()`.** A mean is `ratio(name, sum_of(...), count_of(...))`.
An average of averages has no spelling in this API.

```python
def default_rule(self) -> ReAggregation
@property needs_column -> bool
```

| Aggregate | default rule |
|---|---|
| `SUM` | `ReAggregation.SUM` |
| `COUNT` | `ReAggregation.SUM`  ← partial counts compose by **summing** |
| `COUNT_DISTINCT` | `ReAggregation.NONE` |
| `MIN` / `MAX` | `ReAggregation.MIN` / `MAX` |
| `RATIO` | `ReAggregation.REDERIVE` |

### `ReAggregation(Enum)` — `SUM MIN MAX REDERIVE NONE`

`@property is_provable -> bool` — False only for `NONE`.

### `Dimension` *(frozen)*

```python
Dimension(column: ColumnRef, bucket: TimeBucket|None = None,
          alias: str|None = None, note: str = "")
@property name -> str      # alias, else "dt_week" when bucketed, else the column name
@property source -> Source
@property columns -> frozenset[ColumnRef]
def coarsens_to(self, other: Dimension) -> bool   # other is this column, equal-or-coarser
```

### `Grain` *(frozen)*

```python
Grain(dimensions: tuple[Dimension, ...] = ())
@classmethod of(cls, *dimensions: Dimension | ColumnRef) -> Grain    # bare refs allowed
@property names -> tuple[str, ...]        # output names, Grain order
@property columns -> frozenset[ColumnRef]
@property sources -> frozenset[Source]
@property time_bucket -> TimeBucket | None    # raises if two Dimensions are bucketed
def coarsens(self, other: Grain) -> bool      # "self is at-or-coarser than other"
def comparable(self, other: Grain) -> bool
__len__ / __iter__ / __str__
```
`coarsens` is conservative: any Dimension of `self` not implied by one of `other` is an
immediate `False`, so an unprovable re-grain refuses. Refuses duplicate output names.

### `Filter` *(frozen)*

```python
Filter(name: str, predicate: Predicate, note: str = "")
@property columns / sources / deferred
__and__ / __or__ / __invert__ -> Predicate
```
One type for both uses: a Case-level narrowing (WHERE) and a Metric-scoped `when`
(conditional aggregate). The difference is where it is attached.

### `Metric` *(frozen)*

```python
Metric(name: str, aggregate: Aggregate,
       column: ColumnRef | None = None,
       of_source: Source | None = None,          # required iff column is None
       when: Filter | None = None,               # must filter the SAME Source
       parts: tuple[Metric, Metric] | None = None,   # (numerator, denominator) iff RATIO
       tags: tuple[Tag, ...] = (),
       rule: ReAggregation | None = None,        # None -> aggregate.default_rule()
       note: str = "")

@property source -> Source                # DERIVED from column/of_source/parts
@property reaggregation -> ReAggregation  # rule or the default
@property is_ratio -> bool
@property components -> tuple[Metric, ...]
@property columns -> frozenset[ColumnRef]     # measured + scoped-filter + component
def tagged(self, tag: Tag) -> bool
def rename(self, name: str) -> Metric
```

`__post_init__` refuses: a RATIO without exactly two parts or carrying a `column`; a
non-RATIO carrying parts; an aggregate needing a column without one; a COUNT of rows with
neither `column` nor `of_source`; **a ratio whose parts measure different Sources**; **a
ratio with a non-rolling-up component**; and any Metric reading more than one Source.

### Constructors — prefer these over the initialiser

```python
def sum_of(name, column, *, when=None, tags=(), rule=None, note="") -> Metric
def count_rows(name, source, *, when=None, tags=(), note="") -> Metric        # COUNT(*)
def count_of(name, column, *, when=None, tags=(), note="") -> Metric          # COUNT(col)
def count_distinct(name, column, *, when=None, tags=(), note="") -> Metric    # rule NONE
def min_of(name, column, *, when=None, tags=(), note="") -> Metric
def max_of(name, column, *, when=None, tags=(), note="") -> Metric
def ratio(name, numerator: Metric, denominator: Metric, *, tags=(), note="") -> Metric
```
Only `sum_of` exposes `rule=`, and only as an override. There is no defaultable path to a
wrong Re-aggregation rule.

### `MetricSelection` *(frozen)* — late-bound Tag families

```python
MetricSelection(tags: tuple[Tag,...] = (), names: tuple[str,...] = (),
                excluded: tuple[tuple[str, str], ...] = ())     # (name, reason)
def without(self, *names: str, because: str) -> MetricSelection    # `because` required
def __or__(self, other: MetricSelection) -> MetricSelection
def resolve(self, registry: Registry, *, case: str | None = None) -> tuple[Metric, ...]

def by_tag(*tags: Tag) -> MetricSelection
def by_name(*metrics: Metric | str) -> MetricSelection        # escape hatch; does not scale
```
`resolve` is sorted by Metric name, refuses each empty Tag, refuses an unknown explicit
name, **refuses an exclusion that matches nothing**, and refuses an empty result.

### `Case` *(frozen)*

```python
Case(name: str, metrics: MetricSelection, grain: Grain,
     filters: tuple[Filter, ...] = (),
     via: tuple[str, ...] = (),              # JOIN NAMES, not Source names; a SET
     anchor: str | None = None,              # "db.table" of the spine, when Metrics straddle
     writes_to: Source | None = None,
     note: str = "")

def variant(self, name: str, *, grain=KEEP, metrics=KEEP, filters=KEEP,
            also_filtered_by: Sequence[Filter] = (), via=KEEP, anchor=KEEP,
            writes_to: Source | None = None, note: str = "") -> Case

def resolved_metrics(self, registry) -> tuple[Metric, ...]
def sources(self, registry) -> frozenset[Source]
def referenced_columns(self, registry) -> frozenset[ColumnRef]
def output_names(self, registry) -> tuple[str, ...]   # Grain order, then Metrics sorted
@property deferred -> bool
def predicate(self) -> Predicate | None    # Case-level Filters ANDed; excludes Metric `when`
```

`KEEP` is a module-level sentinel. **`writes_to` is NOT inherited by `variant` - it defaults
to `None`.** Two Cases writing the same Partition would overwrite each other every run, and
that mistake must not be available by omission; `freeze()` now refuses it outright.

`via` is matched as a SET of edges, so nothing inside it may decide anything the order could
change - which is why the spine is `anchor` and not `via[0]`. `__post_init__` refuses a bare
`str` for `via`, because `via=('one_edge')` is the string a contributor gets by pasting a
one-edge candidate without its trailing comma, and iterating it reads every character as a
Join name.

`grain` accepts a tuple of `Dimension | ColumnRef` and normalises to a `Grain`.

### `MetricPlan` *(frozen)* — grain.py's proof

```python
MetricPlan(metric: Metric, target: Grain, rule: ReAggregation,
           native: Grain | None = None,                 # None = atomic rows
           parts: tuple[MetricPlan, MetricPlan] | None = None)
```
`__post_init__`: `REDERIVE` and `parts` appear together or not at all; a `NONE` rule is
only legal when `native` is None or equals `target`.

### `CasePlan` *(frozen)* — the token `compile.render` requires

```python
CasePlan(case: Case, spine: Source, path: JoinPath,
         metrics: tuple[MetricPlan, ...], dimensions: tuple[Dimension, ...],
         filters: tuple[Filter, ...] = (), run_date: date | None = None)
@property sources -> tuple[Source, ...]      # spine first, then path order = FROM/JOIN order
@property join_names -> tuple[str, ...]
@property output_names -> tuple[str, ...]
```
`__post_init__` re-verifies, from its own fields and with no Registry and no graph search:
the path chains from the spine; no Source is visited twice; every MetricPlan targets
`case.grain`. Violations raise `PlanInvariantViolated`.

It deliberately does **not** re-run the ambiguous-path search or the Fan-out walk. This is a
net, not a seal - a hand-built plan naming a valid but arbitrarily chosen Join path still
renders. Build plans with `compile.plan`.

---

## `sqlcomposer/joins.py`

```python
def graph(registry: Registry) -> networkx.MultiGraph
def candidates(registry: Registry, needed: frozenset[Source], *,
               anchor: Source) -> tuple[JoinPath, ...]
def spine(registry: Registry, case: Case) -> Source
def resolve(registry: Registry, case: Case) -> tuple[Source, JoinPath]
def check_fan_out(spine_source: Source, path: JoinPath,
                  metrics: Sequence[Metric]) -> None
def steps_between(spine_source: Source, target: Source, path: JoinPath) -> JoinPath
def fans_out_between(spine_source: Source, target: Source, path: JoinPath) -> bool
def apply(select: exp.Select, path: JoinPath) -> exp.Select
def describe(path: JoinPath) -> tuple[str, ...]
```

* `graph`: MultiGraph (parallel edges must not collapse); nodes are `Source.qualified`; each
  edge carries `step` and is keyed by `JoinStep.name`.
* `candidates`: minimal paths only, oriented from `anchor`, sorted by join names. `()` when
  disconnected; `((),)` when `needed == {anchor}`.
* `spine`: one Metric Source → that one; several → `case.anchor` says which, and without it
  `AmbiguousJoinPath` carrying one `(anchor, via)` pair per possibility. An `anchor` that no
  Metric of the Case measures → `InvalidDeclaration`.
* `resolve`: one candidate → use it; none → `NoJoinPath`; several → `AmbiguousJoinPath`
  unless `case.via` names one. A `via` that forms no valid Join path → `NoJoinPath`, never a
  silent fallback: a name pinned twice, a pinned edge that never becomes walkable, a detour
  through a Source nothing needs. Does **not** check fan-out.
* `apply`: one `JOIN` per step, `join_type` from `JoinStep.kind`, ON from `JoinStep.on()`,
  **no explicit aliases**, returns a new Select.

## `sqlcomposer/grain.py`

```python
def bucket_expression(column: ColumnRef, bucket: TimeBucket) -> exp.Expr
def group_by(grain: Grain) -> tuple[exp.Expr, ...]
def projection(dimension: Dimension) -> exp.Alias
def native_grain(registry: Registry, source: Source) -> Grain | None
def determines(dimension: Dimension, metric: Metric, spine: Source, path: JoinPath) -> bool
def check_regrain(metric: Metric, *, native: Grain | None, target: Grain) -> ReAggregation
def plan_metric(registry: Registry, metric: Metric, target: Grain, *,
                spine: Source, path: JoinPath) -> MetricPlan
def plan_metrics(registry: Registry, metrics: Sequence[Metric], target: Grain, *,
                 spine: Source, path: JoinPath) -> tuple[MetricPlan, ...]
def aggregate_expression(metric: Metric, *, run_date: date | None = None) -> exp.Expr
def reaggregate(rule: ReAggregation, partial: exp.Expr) -> exp.Expr
def rederive(numerator: exp.Expr, denominator: exp.Expr) -> exp.Expr
def render_metric(plan: MetricPlan, *, run_date: date | None = None) -> exp.Alias
```

`check_regrain`'s decision table:

| `native` vs `target` | outcome |
|---|---|
| `native is None` (atomic rows) | compute from scratch; return the partial rule |
| equal | identity; read stored values |
| `target` coarsens `native` | consult `metric.reaggregation`; `NONE` → `UnsafeReAggregation` |
| `native` strictly coarsens `target` | `GrainTooFine` |
| neither coarsens the other | `GrainNotComparable` |

`check_regrain` asks the READING Metric only, which is the whole question against atomic
rows and half of one against a written Source. So `plan_metric` runs a second check when a
re-aggregation is genuinely happening: `Registry.metric_behind` recovers the Metric that wrote the
stored column, and the reading Metric's rule must match its rule or the build fails with
`UnsafeReAggregation(stored_by=<producing metric>)`. Without it, `sum_of(DAILY.failure_rate)`
- a well-formed SUM of a column of DOUBLEs - compiles and returns a wrong number. Silent for
a pre-aggregated Source this library does not write, where `metric_behind` returns None.

* Bucketing renders through `exp.Anonymous` + DATE_FORMAT masks, **never `exp.func`**. WEEK
  is the ISO week anchored to Monday, rendered as that Monday's date.
* `group_by` groups by the **expression**, not by alias or position.
* A Metric with a scoped `when` becomes a conditional aggregate, never a WHERE clause.
* `reaggregate` raises for `REDERIVE` and `NONE`; a ratio goes through `rederive`.

## `sqlcomposer/compile.py`

```python
DIALECT: Final[str] = "hive"
ERROR_LEVEL: Final = sqlglot.ErrorLevel.RAISE

@dataclass(frozen=True)
class Compiled:
    name: str; sql: str; ast: exp.Expr; plan: CasePlan
    lineage: Lineage; run_date: date | None = None

def escalate_sqlglot_logging() -> None
def literal(ref: ColumnRef, value: Value, *, run_date: date | None = None) -> exp.Expr
def render_predicate(predicate: Predicate, *, run_date: date | None = None) -> exp.Condition
def render_metric(plan: MetricPlan, *, run_date: date | None = None) -> exp.Alias
def plan(registry: Registry, case: Case, *, run_date: date | None = None) -> CasePlan
def build(registry: Registry, case_plan: CasePlan) -> exp.Select
def qualify_gate(registry: Registry, ast: exp.Expr, *, case: str = "") -> exp.Expr
def render(ast: exp.Expr, *, dialect: str = DIALECT) -> str
def compile_case(registry: Registry, case: Case, *, run_date: date | None = None) -> Compiled
def compile_metric_only(registry: Registry, metric: Metric, *,
                        run_date: date | None = None) -> str
```

* `plan` order: `require_frozen` → resolve Tag family → `joins.resolve` →
  `joins.check_fan_out` → `grain.plan_metrics`. `run_date` is carried on the plan.
* `build` emits `SELECT <dimensions in Grain order>, <metrics in plan order> FROM <spine>
  <joins> WHERE <Case filters ANDed> GROUP BY <dimension expressions>`. **No ORDER BY and no
  LIMIT** - unsettled scope; the fix would be a field on `Case`, never string manipulation.
* `qualify_gate` always uses `registry.schema()` entire and wraps `OptimizeError` as
  `ResolutionFailed`. The returned tree is backtick-quoted and aliased; golden SQL is
  written against that form.
* `render` is the only `.sql()` call in the library.

## `sqlcomposer/lineage.py`

```python
NodeId = str
ROLE_METRIC = "metric"; ROLE_DIMENSION = "dimension"
ROLE_FILTER = "filter"; ROLE_JOIN_KEY = "join_key"

@dataclass(frozen=True)
class Lineage:
    graph: networkx.DiGraph; case: str; path: tuple[str, ...]
    def outputs(self) -> tuple[str, ...]
    def upstream(self, output_column: str) -> frozenset[NodeId]
    def downstream(self, column: NodeId) -> frozenset[str]
    def columns(self) -> frozenset[NodeId]

def node_id(ref: ColumnRef) -> NodeId                     # == ColumnRef.qualified
def output_id(case: str, output_column: str) -> NodeId    # "<case>:<output>"
def build(registry: Registry, plan: CasePlan) -> Lineage
def to_text(lineage: Lineage, output_column: str | None = None) -> str
def to_dot(lineage: Lineage, name: str = "lineage") -> str

@dataclass(frozen=True)
class Manifest:
    source: str; written_by: str; written_at: Grain; lineage: Lineage
    def to_json(self) -> str
    @classmethod from_json(cls, text: str, registry: Registry) -> Manifest

def manifest_for(registry: Registry, plan: CasePlan, target: Source) -> Manifest
def manifests_for_reads(registry: Registry, case: Case) -> tuple[Manifest, ...]
def trace_through(lineage: Lineage, manifests: Sequence[Manifest]) -> Lineage
def static_lineage(registry: Registry, case: Case) -> str
def write_static_lineage(registry: Registry, directory: str | Path) -> tuple[Path, ...]
def write_manifests(registry: Registry, directory: str | Path) -> tuple[Path, ...]
```

`static_lineage` emits TWO trees for a Case that reads a written Source: `as read:`, which
stops at the written table because that is what the statement reads, and `traced to source:`,
which is the same tree spliced through that table's Manifest. Both are derived from the
Declarations with nothing running and no `run_date`, and `write_manifests` is the writer
`Manifest.from_json` needs in order to be readable by another process at all.

**Graph contract — do not vary this.**

* Node ids: `db.table.column` for Source columns, `<case>:<output>` for outputs. They cannot
  collide (a Case name may not contain `:`; a qualified column has exactly two dots).
* Edges point **downstream**, source column → output, so `networkx.ancestors(graph, output)`
  answers "where did this number come from".
* Node attrs: `kind` (`"column"` | `"output"`) on every node; `type`, `partition` on a
  column; `role` (`"dimension"` | `"metric"`), plus `rule` and `native` on a metric output.
* Edge attrs: `role` (one of the four constants); `filter` on a filter edge; `metric` on a
  metric edge.
* Edges added by `build`: Metric columns → its output (`metric`); Dimension column → its
  output (`dimension`); each Case-level Filter's columns → **every** output (`filter`); a
  Metric-scoped `when`'s columns → that Metric's output only; each join key on both sides →
  every output (`join_key`).

Builder-derived lineage is **authoritative**. `sqlglot.lineage` appears only in the test
suite as a cross-check, never at runtime - it disables qualify's validation internally and
degrades silently (placeholder leaves, `"*"` leaves, warnings for unknown scopes).

## `sqlcomposer/write.py`

```python
class StatementKind(Enum): SELECT = "SELECT"; CTAS = "CTAS"; INSERT_OVERWRITE = "INSERT_OVERWRITE"

@dataclass(frozen=True)
class Statement:
    kind: StatementKind; sql: str; target: str | None; purpose: str
    partition: tuple[tuple[str, str], ...] = ()      # (column, rendered literal text)

@dataclass(frozen=True)
class StatementPlan:
    statements: tuple[Statement, ...]; manifests: tuple[Manifest, ...] = ()
    def __iter__(self) -> Iterator[Statement]
    def __len__(self) -> int
    def to_script(self) -> str

def partition_values(registry: Registry, case: Case, *, run_date: date,
                     partition: Mapping[str, Value] | None = None
                     ) -> tuple[tuple[str, Value], ...]
def insert_overwrite(registry: Registry, case: Case, *, run_date: date,
                     partition: Mapping[str, Value] | None = None) -> Statement
def create_table_as(registry: Registry, case: Case, *, run_date: date) -> Statement
def plan(registry: Registry, cases: Sequence[Case], *, run_date: date,
         partition: Mapping[str, Value] | None = None) -> StatementPlan
```

* `INSERT OVERWRITE TABLE db.tgt PARTITION(dt = '...') SELECT ...`, built as
  `exp.Insert(this=..., expression=..., overwrite=True, partition=exp.Partition(...))`.
  A retry converges instead of double-counting; that is the whole reason for the mode.
* Partition values render through the **target** column's `Column.literal` - bare literal,
  never a CAST, or every subsequent read of the table loses pruning.
* SELECT column order is `Case.output_names`; Hive matches INSERT columns by position.
* A Partition column left without a value raises `InvalidDeclaration` - a dynamic partition
  overwrites whatever the SELECT produced.
* `plan` topologically sorts by `written_by` dependency, ties broken by Case name; a cycle
  raises `InvalidDeclaration`.

## `sqlcomposer/verify.py`

```python
@dataclass(frozen=True)
class WarehouseColumn:
    name: str; type: str; partition: bool = False; nullable: bool = True

Describe = Callable[[Source], Sequence[WarehouseColumn]]

class DriftKind(Enum):
    ADDED; DROPPED; RETYPED; PARTITIONING_CHANGED; NULLABILITY_CHANGED; SOURCE_MISSING

@dataclass(frozen=True)
class DriftItem:
    kind: DriftKind; source: str; column: str | None
    declared: str | None; actual: str | None
    referenced: bool; used_by: tuple[str, ...] = ()
    @property breaking -> bool

@dataclass(frozen=True)
class DriftReport:
    items: tuple[DriftItem, ...]
    @property breaking -> tuple[DriftItem, ...]
    @property clean -> bool
    def raise_if_breaking(self) -> None      # BreakingDrift
    def to_text(self) -> str

def referenced_columns(registry: Registry) -> Mapping[str, frozenset[str]]
def cases_using(registry: Registry, ref: ColumnRef) -> tuple[str, ...]
def compare(registry: Registry, source: Source,
            actual: Sequence[WarehouseColumn]) -> tuple[DriftItem, ...]
def verify(registry: Registry, describe: Describe) -> DriftReport
```

* `breaking` = `DROPPED | RETYPED | PARTITIONING_CHANGED | SOURCE_MISSING` **and**
  `referenced`. `ADDED` is never breaking.
* Type comparison normalises case and internal whitespace: `decimal(18, 2)` ==
  `DECIMAL(18,2)`.
* A `describe` that raises for a Source yields one `SOURCE_MISSING` item rather than
  propagating.
* `verify` never raises on drift; `raise_if_breaking()` is a separate decision.

## `sqlcomposer/runner.py`

```python
@runtime_checkable
class Runner(Protocol):
    def run(self, sql: str) -> pandas.DataFrame: ...

def execute(runner: Runner, statements: Sequence[Statement]) -> list[pandas.DataFrame]
def execute_plan(runner: Runner, plan: StatementPlan) -> list[pandas.DataFrame]
def frame(runner: Runner, compiled: Compiled) -> pandas.DataFrame
```

Convenience only. **Nothing in the core imports this module** - that is worth a test. One
finished SQL string, no `params`: the external API takes one string and the scheduler does
not substitute values into SQL text, both recorded assumptions rather than supplied facts.
No retry loop here, ever - the scheduler owns retries and INSERT OVERWRITE is what makes
them safe. pandas is imported under `TYPE_CHECKING` only.

---

## Import layering

```
errors           (no sqlglot)
  └── declaration        (sqlglot: exp, MappingSchema; imports model lazily inside methods)
        └── model        (no sqlglot)
              ├── joins        (networkx, exp)
              ├── grain        (exp)
              ├── lineage      (networkx)
              │     └── compile        (sqlglot; imports joins, grain, lineage)
              │           └── write    (imports compile, lineage)
              │                 └── runner   (pandas under TYPE_CHECKING only)
              └── verify
```

`declaration.Registry` stores `Metric`, `Filter` and `Case`, which live in `model`. It
imports them **inside** `add()`, `from_modules()` and `native_grain()` rather than at module
scope. That is not a cycle: by the time anyone holds a Metric, `model` has finished
importing. Do not lift those imports to the top of the file.

---

## Worked example

```python
from sqlcomposer.declaration import Cardinality, Column, Join, Registry, RunDate, Source, TimeBucket
from sqlcomposer import model as m

COURIERS = Source(db="mart", table="couriers", one_row_per="courier", columns=(
    Column("courier_id", "STRING", nullable=False),
    Column("courier_name", "STRING"),
    Column("city", "STRING"),
    Column("is_test", "BIGINT", nullable=False),
))

DELIVERIES = Source(db="mart", table="deliveries", one_row_per="delivery attempt", columns=(
    Column("delivery_id", "STRING", nullable=False),
    Column("courier_id", "STRING", nullable=False),
    Column("dt", "STRING", partition=True, nullable=False, note="yyyy-MM-dd"),
    Column("failure_reason", "STRING", note="NULL means delivered"),
    Column("fee_amount", "DECIMAL(18,2)", nullable=False),
), joins=(
    Join(to="mart.couriers", keys=(("courier_id", "courier_id"),),
         cardinality=Cardinality.MANY_TO_ONE),
))

DELIVERY_HEALTH = "delivery_health"

FAILED    = m.Filter("failed", DELIVERIES.failure_reason.is_not_null())
LAST_7    = m.Filter("last_7_days", DELIVERIES.dt.between(RunDate() - 6, RunDate()))
LIVE      = m.Filter("live_couriers", COURIERS.is_test.eq(0))

ATTEMPTS  = m.count_rows("delivery_attempts", DELIVERIES, tags=(DELIVERY_HEALTH,))
FAILURES  = m.count_rows("failed_deliveries", DELIVERIES, when=FAILED, tags=(DELIVERY_HEALTH,))
RATE      = m.ratio("failure_rate", FAILURES, ATTEMPTS, tags=(DELIVERY_HEALTH,))

BY_DAY     = m.Dimension(DELIVERIES.dt, TimeBucket.DAY)
BY_WEEK    = m.Dimension(DELIVERIES.dt, TimeBucket.WEEK)
BY_COURIER = m.Dimension(COURIERS.courier_name, alias="courier")

HEALTH_BY_COURIER = m.Case(
    name="health_by_courier",
    metrics=m.by_tag(DELIVERY_HEALTH),
    grain=m.Grain.of(BY_DAY, BY_COURIER),
    filters=(LAST_7, LIVE),
)

# The second Case is four lines, and they ARE the difference.
HEALTH_BY_CITY = HEALTH_BY_COURIER.variant(
    "health_by_city",
    grain=m.Grain.of(BY_WEEK, m.Dimension(COURIERS.city)),
    also_filtered_by=(m.Filter("eu_only", COURIERS.city.isin("Berlin", "Madrid")),),
)

REGISTRY = Registry().add(
    COURIERS, DELIVERIES, FAILED, LAST_7, LIVE,
    ATTEMPTS, FAILURES, RATE,
    HEALTH_BY_COURIER, HEALTH_BY_CITY,
).freeze()
```

What that buys, checked:

```python
DELIVERIES.fee_amonut              # UndeclaredColumn at import, did_you_mean=["fee_amount"]
DELIVERIES.dt.eq(20260917)         # LiteralTypeMismatch at import (STRING column)
DELIVERIES.dt.eq(RunDate())        # -> dt = '2026-09-17'      bare literal, pruning survives
COURIERS.city.isin("Mad'rid")      # -> IN ('Mad\'rid')         escaped by sqlglot
# and on a declared TIMESTAMP column that is NOT a Partition column:
#   delivered_at.ge(date(2026, 1, 2))  ->  delivered_at >= CAST('2026-01-02' AS DATE)
REGISTRY.tagged("delivery_helth")  # EmptyTagFamily
HEALTH_BY_COURIER.output_names(REGISTRY)
# ('dt_day', 'courier', 'delivery_attempts', 'failed_deliveries', 'failure_rate')
```

Declaring `m.count_distinct("couriers_active", DELIVERIES.courier_id, tags=(DELIVERY_HEALTH,))`
in **any** scanned module adds it to both Cases with no Case edited - and makes either Case
raise `UnsafeReAggregation` the moment it is re-grained off a written Source. That is the
correct outcome, loudly.
