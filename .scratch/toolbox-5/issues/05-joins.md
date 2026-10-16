# Joins

Type: task
Status: resolved
Blocked by: 01
Size: M

## Question

Map family 5. `SEMI_JOIN` (LEFT SEMI JOIN; only the reading side's columns selectable),
`ANTI_JOIN` (LEFT JOIN ... WHERE key IS NULL), `FULL_JOIN`, `JOIN(..., broadcast=True)` (MAPJOIN
hint); `RIGHT_JOIN` refused, its fix the swapped LEFT_JOIN. Keys carried through each (ticket 01).

## Done when

- Each join's Hive and rows in both Editions; the Example database gains a table for FULL_JOIN
  to reconcile if it needs one; a how-to on semi-, anti- and full joins.
- Both runs pass, the code-review skill has run with this ticket as its spec, its drift items are
  closed, and the beginner reader has run on what a beginner sees (CLAUDE.md's Definition of done).

## Answer

Built on branch `worktree-agent-aa687d203297246a7`, from dev e82a55a, in the commit that
resolves this ticket.

**What was built**

- **Clause functions** in `composer_core/clauses.py`, beside JOIN and LEFT_JOIN, with the
  larger logic in a new core file, `composer_core/joins.py` (registered in
  `tools/editions.py`): how each join is written (`HOW`), the anti join's NULL test, the
  checks statement(...) runs, and the refusals. clauses.py otherwise gains only a `broadcast`
  slot on Clause, the new names in `JOINS`, one `check_joins(s)` call in statement(...) and
  two lines in `read_spans`.
  - `SEMI_JOIN(t, ON=..., reads_all_partitions=, broadcast=)`: written `LEFT SEMI JOIN`;
    never repeats rows, so no repeated-rows Warning and no `many_matches=`.
  - `ANTI_JOIN(t, ON=..., reads_all_partitions=, broadcast=)`: written `LEFT JOIN ... ON ...`
    plus `<t's column> IS NULL` ANDed after the Statement's own WHERE. The column tested is
    one ON= sets equal to another table's column, else to anything that doesn't read t (a
    value); an ON= with neither is refused at the call.
  - For both, only their own ON= may read t's columns: SELECT, WHERE, GROUP_BY, HAVING,
    ORDER_BY or another join's ON= reading one is refused (ValueError), naming the place
    and the join to use instead (JOIN to show a semi-joined column, LEFT_JOIN an anti-joined
    one). Their Date partition is bounded inside ON=, as LEFT_JOIN's.
  - `FULL_JOIN(t, ON=..., keeps_only_matches=, many_matches=, reads_all_partitions=)`:
    written `FULL JOIN`. A WHERE condition on a table read at or before it is a Guard
    (`guard_full_join_then_where`), unless it keeps unmatched rows (`is_null`, or `any_of`
    holding one), opt-out `keeps_only_matches=True`. A side with a Date partition can be
    bounded neither in WHERE nor ON=: the Load limit's fix says to read it through a Derived
    table (for the FROM side too, `joins.full_joined`). The repeated-rows Warning works as
    JOIN's.
  - `RIGHT_JOIN(...)`: always refused, its fix the LEFT_JOIN with the tables swapped.
  - `broadcast=True` on JOIN, LEFT_JOIN, SEMI_JOIN and ANTI_JOIN (not FULL_JOIN, which Hive
    can't map-join): `SELECT /*+ MAPJOIN(a, b) */ [DISTINCT]` in the step that joins them, a
    new `broadcast` part of the Select tree. sqlglot's Hive drops hints, so sqlglot Composer
    writes through a copy of the Hive dialect with `QUERY_HINTS` on; Spark Composer writes it
    itself and its read-back accepts exactly that hint. JOIN's docstring says Hive makes map
    joins by itself with the shipped "map_joins" Session setting, and heeds the hint only once
    `hive.ignore.mapjoin.hint` is false (a set of the user's own).
- **Keys** (`keys.py`): a SEMI_JOIN or ANTI_JOIN keeps the reading table's Key (`_keeps`);
  a FULL_JOIN loses it ("FULL_JOIN(t, ON=...) keeps the rows of each side that have no
  match, with NULL in the other side's columns"), a row_number's Key or a GROUP_BY giving one
  back. A write through a semi or anti join is let through; one from a full join needs a
  GROUP_BY.
- **Lineage**: each new join's ON= box is labelled with what it keeps, such as "ANTI JOIN ON
  (keeps the rows with no match)"; its Keys section says where a FULL_JOIN lost the Key.
- **Example database**: a seventh table, `ops.scheduler_runs` (run_id, job_id, dt; Key
  run_id), the scheduler's record of the two days' runs, lacking run 99 and holding a run 100
  job_runs lacks, for FULL_JOIN to find. sqlglot's executor would run a LEFT SEMI JOIN as a
  LEFT JOIN, so sqlglot Composer's Example database refuses it ("its executor has no LEFT SEMI
  JOIN"); Spark Composer's runs it. Both answer the anti and full joins the same (tested).
- **Docs**: docstrings with examples (first lines are the cheat-sheet lines); how-to 33
  "Semi-, anti- and full joins" (Intermediate 19-33; a pandas stand-in for the semi join on
  sqlglot Composer); CHANGES 5.0 New; CONTEXT's new word **Map join**; the README template's
  table count. Golden corpus `edge:joins:*` cases (Hive, refusals, broadcast with backticked
  names, in a Derived table, two tables, before DISTINCT, a write through semi and anti
  joins). Galleries, how-to pages and Example projects regenerated.
- **Tests**: `tests/test_joins.py` (Hive, rows in both Editions, refusals, Keys, by_day,
  Lineage), `test_guard_full_join_then_where_refuses`/`_opt_out` in test_refusals, the
  public-name list (71), the Example database's table list.

**Code review** (code-review skill, since e82a55a, before the commit).
Standards: no hard violation. Fixed: "map join" made a glossary word (CONTEXT); the
double negative about hive.ignore.mapjoin.hint and "needn't be sorted to meet it"
reworded; the broadcast refusal now says what broadcast does (`need_broadcast_true_or_false`,
one caller, no longer generic); FULL_JOIN's reflowed sentence; refusals.py's module
docstring ("your own join's line"); Lineage's label words moved into lineage.py;
`tested_column`'s list made a plain variable. Kept: join kinds as `read._name` strings and
their small tables (`HOW`, `ONLY_TESTS`, `BOUNDED_IN_ON`, sqlglot's `_JOINS`), as the code
already keys every clause by name, a plain-function shape the standards prefer to a class
per join; `load_limit_date_bound` keeps its own `startswith` tuple, since refusals.py can't
import joins.py (joins.py imports it); the dialect copy in sqlglot_composer/writing.py is
internal.
Spec: Fixed: a FROM table with days under a FULL_JOIN got "Bound it in WHERE", which the
Guard then refused: now the Derived-table fix (`full_joined`), tested; ANTI_JOIN's column
matched to a calculation of another table (`equals(t.x, other.y + 0)`) was refused as
having no equals: now tested. Answered: broadcast= on LEFT_JOIN, SEMI_JOIN and ANTI_JOIN
goes past "JOIN(..., broadcast=True)", kept since each is a valid map join and the
parameter reads the same; a later JOIN whose ON= reads a FULL_JOIN side can still drop the
other side's unmatched rows, as a later JOIN after LEFT_JOIN can today (left for a ticket
of its own if wanted); Lineage treats FULL JOIN's ON= as deciding every column's rows,
which holds for every column read from either side (it decides where NULL appears and what
pairs). sqlglot Composer's Example database can't run SEMI_JOIN: see the open question.

**Beginner reader:** [report](../reports/05-beginner-reader.md). Fixed: how-to 33's
sqlglot-only note now says the semi join's `run` stops with a RuntimeError when pasted, at
the step and in Check it worked; broadcast's docstring and how-to say which joins take it,
what a worker and a hint are, and how to make Hive heed it (a `hive_settings` set of your
own, shown run); FULL_JOIN's docstring says when its opt-out is right, that `any_of` of
`is_null`s is allowed, and how to GROUP_BY for a Key (with the call); the example's column
renamed `in_scheduler_runs`; the first lines of SEMI_JOIN, FULL_JOIN and RIGHT_JOIN
reworded; SEMI_JOIN says why LEFT; ANTI_JOIN says which column is tested and why it never
repeats rows; both ANTI_JOIN refusals reworded; CHANGES' "so"; the Example database's
docstring counts its tables plainly; how-to 33's "no RIGHT_JOIN". Left: the
`keeps_only_matches=` name on FULL_JOIN (kept for one opt-out name across LEFT_JOIN and
FULL_JOIN, its docstring now says what it lets through); the Lineage label "ANTI JOIN ON"
beside Hive's LEFT JOIN (the label names the clause the user wrote, as for every join); the
sqlglot executor's generic "try the Statement here without that part".

**Open for the user**

- sqlglot Composer's Example database can't run a `LEFT SEMI JOIN`: sqlglot's executor runs
  it as a LEFT JOIN, so it is refused, and how-to 33 shows a pandas result, as for windows.
  Spark Composer's runs it. Rewriting a semi join for the executor (as a JOIN to a SELECT
  DISTINCT of ON='s columns) works only for plain equals matches, so it wasn't done.
- broadcast= is ignored by Hive while `hive.ignore.mapjoin.hint` is true, its default.
  Should a shipped Session setting set it to false (or should "map_joins" include it)?
- Ticket 07 (stacking) may add an Example database table too, for EXCEPT: `ops.scheduler_runs`
  may serve it, and the two edits to `example_database.py`'s table list will meet at merge.
