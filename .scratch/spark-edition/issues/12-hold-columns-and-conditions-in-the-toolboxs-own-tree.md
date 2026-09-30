# Hold Columns, Conditions and sort keys in the Toolbox's own tree

Type: task
Status: resolved
Blocked by: 11

## Question

Replace the sqlglot trees in `Column._tree`, `Condition._tree` and the ORDER BY keys with
`trees.Node`, keeping SQL Composer's output byte-identical on every sqlglot version in range.

`sql_composer/trees.py` (shared):

- `Node(kind, **parts)`, with meta, `set`, `copy`, structural `==`, a breadth-first `walk` and
  `find_all` over parts in their written order, `flatten`, and `.name`/`.table` on columns. It has
  no `__len__` or `__bool__`, and `__hash__ = None`, as sqlglot's trees don't hash either.
- A closed set of KINDS, with sqlglot's shapes, because lineage orders its boxes and arrows by a
  breadth-first walk (`sql_composer/lineage.py:153`, `:174`): binary, left-deep AND/OR with
  sqlglot's `_combine` bracket rule; `Paren` from `tables._bracketed`; `Case` holding `If`;
  `Count(Distinct)`; `Not(In)`; `Not(Is Null)`; `Window(RowNumber, partition_by,
  Order[Ordered])`; `Alias`; `Var`.
- `HiveFunction(name, args as written, aggregate)`: calls are compared and walked as written (the
  user's decision), so `hive_function("nvl", ...)` no longer equals `fill_null(...)`. This gets a
  CHANGES line.
- `Call` for the five Toolbox date calls (date_sub, next_day, trunc, unix_timestamp,
  from_unixtime).
- `HIVE_AGGREGATES` and the shared hive_function argument-count table move here.

`sql_composer/writing.py` gains `to_sqlglot(node)`, which **replays** today's exact sqlglot calls
(`Literal.string/number`, `to_identifier`, `exp.column`, `exp.alias_`, `exp.func(...,
dialect="hive")` for the date calls, and the hive_function read-back cached by text), never a
generic constructor, so the sqlglot trees themselves stay identical. `tables.readable` stays
shared: it copies the tree top-down, replaces each noted node with a `Var` holding its call, and
calls `hive_text`.

Tests: `tests/sqlglot_edition/test_sqlglot_trees_match.py` checks, over every corpus tree, the
column order against `to_sqlglot(node).find_all(exp.Column)`, pairwise `==`, `has_aggregate`
against the old function, the flatten of ON, and window partition names.
`tests/test_trees.py` tests `Node` on hand-built nodes. The f-string AST rule extends to `Node(...)`
and `trees.*` calls.

## Done when

The Definition of done in `CLAUDE.md` holds; the golden, `examples.html` and every doctest are
byte-identical; the parity tests pass; pytest is green at both ends; the ticket lists every
semantic difference from 2.1.

## Answer

`sql_composer/trees.py` holds `Node`: a kind from a closed list (`KINDS`), its parts by name in
a fixed order, and notes in `meta` that aren't part of the Hive (`3a1be89`). It has:

- structural `==`, which ignores notes and empty parts;
- `copy`, `set`, a breadth-first `walk` and `find_all`, `flatten` and `unnest`;
- `replaced`, which `readable` uses to write each Toolbox call in its Node's place;
- `.name` and `.table`;
- no hashing, `__len__` or `__bool__`.

`combined` joins conditions with AND or OR the way SQL Composer always has: left to right, with
an AND or OR inside put in brackets. `has_aggregate`, the name rules and `HIVE_AGGREGATES` live
there too. Every column, condition, calculation and sort key is a Node now. The date calls are
`Call` nodes, and hive_function is `HiveFunction(name, args, aggregate)`.

`writing.to_sqlglot` replays a Node with the calls SQL Composer always made: `Literal.string` and
`Literal.number`, `exp.column` over `identifier`, `exp.alias_`, `exp.func(..., dialect="hive")`
for the date calls, and hive_function's call read back once and cached by its Hive. The golden,
`examples.html` and every doctest are byte-identical at both ends of the sqlglot range.
`tests/sqlglot_edition/test_sqlglot_trees_match.py` checks every one of the 1,621 corpus trees
against its sqlglot tree: the order of its columns, `==` over 400 of them pairwise, adding up,
what ON='s AND joins, and window partitions. `tests/test_trees.py` tests Node by hand.

**The semantic differences from 2.1**, both from the user's decision that hive_function is
compared and walked as written:

- **Equality.** `hive_function("nvl", x, 0)` no longer equals `fill_null(x, 0)`. Both write
  COALESCE, but one is a HiveFunction and the other a Coalesce. The same goes for any call sqlglot
  rewrites into another function's form, such as `regexp_extract` with and without the group it
  takes by default. A function's name is compared whatever its case, as Hive reads it. It shows in
  one place: a `derived(...)` table that SELECTs one and groups by the other no longer knows its
  key, so a JOIN to it warns. The GROUP BY Guard still lets such a Statement through, because the
  column the call uses is grouped. A CHANGES line says so.
- **Lineage order, below sqlglot 30.19.** The lineage walks a hive_function's arguments as
  written. On sqlglot 25.24.2, DATEDIFF read back as `DATEDIFF(TO_DATE(TO_DATE(a)), ...)`, so its
  columns sat deeper than others and came later: `hive_function("datediff", r.dt, j.team) +
  r.run_id * 2` lists `run_id` last now, where 2.1 listed it first. At the pin, 30.19.0, no corpus
  tree changes.

The shared hive_function argument-count table isn't here yet. Nothing checks against it before
Spark Composer's printer (ticket 17) and the 3.0 change (ticket 25), so it arrives with ticket 17.

## Comments

**Code review (2026-09-29), `3a1be89`.**

- *Spec:*
  - **Fixed:**
    - The CHANGES line said "give GROUP_BY the one you SELECT" as if a Guard refused the mix. It
      now names the one effect, a Derived table's key and the JOIN warning that follows.
    - `hive_function("NVL", ...)` and `hive_function("nvl", ...)` were no longer equal. The name
      is kept in lower case now, since Hive reads it whatever its case.
    - A `Call` names only one of the five date functions.
    - Equality is checked for every pair of corpus trees of the same kind (trees of different
      kinds are never equal in either form), not only the first 400.
  - **Answered, not changed:** there was no argument-count table to move. Ticket 17, whose
    printer is the first thing to check against it, adds it to `trees.py`.
- *Standards:*
  - **Fixed:**
    - trees.py no longer says "rules", a word the glossary keeps for Guards.
    - writing.py's table of builders is `_REPLAY`, not `_BUILDERS`: "builder" is kept for
      Clause functions.
    - trees.py's docstring no longer names SQL Composer, which `swap()` would have made false
      in Spark Composer's copy.
    - `read_back_function` is `function_adds_rows_up`, which says what it returns.
    - `copy` is `replaced` with no stand-ins, so the rebuild is written once.
    - `string(...)` and `number(...)` build every literal.
    - `find_all` refuses a kind that doesn't exist, so a typo can't quietly match nothing.
    - A test holds `_REPLAY` to every kind.
  - **Answered, not changed:**
    - The parts keep sqlglot's names ("this", "expression"). The shapes must match part for
      part, and the Spark printer ports sqlglot's layout by the same names.
    - Callers read `.parts["..."]` where a part isn't a column's name or table. It reads plainly,
      and properties for every part would be machinery.
    - trees.py holds the name rules and `HIVE_AGGREGATES` beside Node: these are what both
      Editions write by, and the ticket put them there.
    - `has_aggregate` and writing.py's `_tree_adds_rows_up` apply one rule to two kinds of tree.
      One is shared, and the other exists only to work out a hive_function's flag with sqlglot.
    - `tables._bracketed` and `trees._bracketed_connector` look alike, but they bracket
      different kinds for different reasons.

**Beginner reader (2026-09-29):**
[reports/12-beginner-reader.md](../reports/12-beginner-reader.md). Answered:

- The CHANGES line's three stops: it says what the change is ("compared as you wrote it") and
  where it shows (a Derived table's key and a JOIN warning). The lineage sentence, true only for a
  call with nothing nested, is gone.
- trees.py says the reader never needs it, why the parts are fixed (so a Statement's lineage
  doesn't change), and that a HiveFunction never equals a Coalesce. "Brackets" are "round
  brackets, ( )". `replaced` has no "it", `.name` says it is a function's name on a call,
  `has_aggregate` says what a window is, and `set` has a docstring.
- The GROUP BY Guard lets `SELECT COALESCE(status, 'x') ... GROUP BY UPPER(status)` through, which
  Hive refuses. 2.1 did the same, so it is outside this ticket, and is flagged as a task of its
  own.
