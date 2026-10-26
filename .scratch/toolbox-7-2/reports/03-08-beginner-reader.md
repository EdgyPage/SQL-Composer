# Beginner reader: Toolbox 7.2 tickets 03 and 08

Read 2026-10-26 after the merges (1078a08, 7aba998) and b158071, every docstring example and
variants run in `.venv`. Saved by the session (the reader writes no file). Line numbers are
b158071's.

## Ticket 03: unchecked_column, unchecked_condition, unchecked_derived

1. Cheat sheet: "no clause function writes it yet" beside "no Toolbox function writes yet":
   different things?
2. "{name}" in the docstring is the notation, but the refusal fixes use a placeholder literally
   named `name`, and an RLIKE condition in unchecked_column's refusals.
3. The condition example can't run on the Example database (three chained tracebacks, then a
   fine four-part message), and the docstring doesn't say so; nor does unchecked_derived's
   (LATERAL VIEW). The failed run still wrote an Admin log beside the notebook.
4. unchecked_derived's example: LATERAL VIEW, explode, `t AS s` and the alias r unexplained; the
   statuses hold no `_`, so "steps" means nothing; LATERAL VIEW sits alone on its line.
5. Three placeholder styles in one family: unchecked_hive takes an f-string; unchecked_column
   placeholders (an f-string refused, with a good fix); unchecked_derived neither (an `id=`
   argument gives a raw TypeError), and takes f-strings silently.
6. A bug: braces are accepted where sqlglot can't write them back:
   `unchecked_derived("d", "SELECT {id} AS run_id ...", ...)` and
   `unchecked_column("{{'k': {a}}}", a=...)` pass, and fail at to_hive with a raw
   `UnsupportedError: Hive does not support named structs.` (costliest 2).
7. Text that isn't Hive is rewritten: `{a} ILIKE 'x%'` becomes `LOWER(...) LIKE LOWER('x%')`,
   `{a}::int` becomes a CAST: more than "capitals".
8. A refusal shows sqlglot's own reason: "Required keyword: 'expression' missing for <class
   'sqlglot.expressions.core.Add'>".
9. `unchecked_column("upper({})", jobs.team)` gives Python's "takes 1 positional argument".
10. A condition that isn't one, `unchecked_condition("upper({t})", ...)`, is taken; and an
    unchecked_column used in WHERE is refused without naming unchecked_condition.
11. The partition Warning's opt-out, reads_all_partitions=True, is named for the opposite of
    what it says ("once you have checked the Unchecked expression filters them").
12. The LEFT_JOIN Warning says `{x} IS NULL` (whose x?), and its only opt-out,
    keeps_only_matches=True, would be untrue when the condition keeps the NULL rows (stuck).
13. The Warning for reading an Unchecked derived table fires for `SELECT DISTINCT team FROM
    ops.jobs`, though ops.jobs isn't partitioned.
14. Joining an Unchecked derived table that already groups: the fix says to group it, the only
    opt-out, many_matches=True, says the opposite of what's true, and there's no key= on
    unchecked_derived (costliest 3).
15. help(set_admin_log) and the Admin log's header don't mention these pieces.
16. repr(unchecked_column(...)) gives no sign it's unchecked; a calculation passed in prints its
    bracket on lines of its own.
17. CHANGES: "one built on LATERAL VIEW" is clear only to someone who knows LATERAL VIEW.

## Ticket 08: compare_hive and compare_with_original

1. "the Hive it was converted from": converted by what? No Conversion in 7.2's names yet, and
   no glossary entry.
2. "each table is called by its own name, and where a query reads one table alone, its columns
   by theirs": understood only by comparing outputs.
3. "such as a <> written as NOT ... = :" reads as a typo.
4. "first at line 6 of each" counts lines of a text never shown (to_hive's differs).
5. The first differing line can mislead (an extra column shows as "status," against
   "status"); conditions in another order count as different.
6. A parse failure ends with "..", and "INNER and OUTER in a join" assumes LEFT OUTER JOIN =
   LEFT JOIN is known.
7. The Worked example's reads_all_partitions=True on FROM, then partition= on the comparison,
   isn't explained.
8. A Statement that filters its own partition (WHERE dt = ..., dt not selected) can't be
   compared: no partition= is refused, the fix names run_id, partition={"dt": ...} isn't a
   column it gives, and reads_all_partitions=True then reports "in every Partition", which is
   false (costliest 1). A write with a static partition= hits the same wall.
9. where= (as check_key takes it) is refused without pointing to partition=.
10. A Verdict whose ok is False is truthy: `if compare_hive(...)` always passes.
11. A NULL prints as None in one table and NaN in another.
12. "Its Hive written by hand, which the Toolbox can't look inside: ..." isn't a sentence,
    shows even when the rows match, and the docstring doesn't say so; the Admin log entry
    doesn't say it came from a comparison.
13. The comparison query can't be previewed; when the original uses what the Example database
    lacks, the fix points at the Statement.
14. A positional query gives Python's "takes 2 positional arguments".

## The three costliest

1. compare_with_original and a Statement that filters its own partition (08, 8).
2. Late raw sqlglot errors from braces sqlglot can't write (03, 6, with 5).
3. Joining an Unchecked derived table (03, 14); runner-up compare_hive's "line 6" (08, 4).

## What was done

See tickets 03's and 08's Reviews.
