# What ticket 18's usability round found, fixed, then everything tested again

Type: task
Status: resolved
Blocked by: 18
Size: M

## Question

The user (2026-11-01), of what ticket 18's round found: "Fix all the issues you found ... Edit
the Excel files if necessary, test all again." None failed a run; each cost a run time or a
guess (`.scratch/usability-loop/results.md`, "The ticket 18 round").

## Done when

- **Excel's AND() and OR().** Copilot file 11 says `AND(a, b)` is `a AND b`, `OR(a, b)` is
  `a OR b` and `NOT(x)` is `NOT x`, where it now says they are as they are. A Conversion that
  can't read its Hive says so, naming the statement's script and line and what sqlglot found,
  with Hive's operator form when it holds `AND(` or `OR(`, in place of "its Hive writes no
  table". An Excel evaluation task holds an IF over an AND() and an OR().
- **Running some of a notebook's cells.** The usability loop's message, and its runner's help,
  say each run starts with nothing defined, so the imports cell, the names cell and, from a
  Decision on, the decisions cell go with every step.
- **check_key on a partitioned table.** `admin/check_references.ipynb` checks a partitioned
  table's Key on its latest Partition, as SHOW PARTITIONS lists it, printing which, in place of
  a call holding `<a value>`. The README's check step says a partitioned table's Key is checked
  with `where=` on a Partition, and how to list them.
- **Comparing a conversion.** A table's `conversion/compare.md` keeps one result for each
  Partition compared: a compare of another Partition adds its result, and one of the same
  Partition, or one after the table is written again, replaces what it would leave stale. It
  passes only when every result kept passes. The convert Workflow's compare step and the
  README's convert section say one Partition is compared, and how to compare another.
- **The warehouse connection.** `warehouse.py`'s docstring and the README's and Start a
  Project's connection step say how to reach a connection kept in a file outside the Project;
  the 8.2 Upgrade step writes the new `warehouse.py` where it is still as 8.0's start() wrote
  it.
- Everything tested again: the full pytest; the Copilot and Excel evaluations, arm C, dev then
  held-out once; the usability loop, each dev scenario three times and each held-out one once.

## Answer

- **AND() and OR().** File 11 writes them as operators, OR bracketed, and its self-check holds
  no AND(, OR( or NOT(. Hive sqlglot can't read, when a batch writes nothing for it, is
  refused naming its file (none for Hive given as text), sqlglot's line counted from the
  Hive's first, and what sqlglot found; an Excel AND( or OR( where a value starts gets Hive's
  operator form as its fix, and other Hive "correct the Hive there". Statements of a batch
  that writes a table besides stay Unchecked statements, as before.
- **The user's ask, mid-work: operators and conditions over ranges, tested.** Six Excel tasks
  (X79 to X84, 84 in all, 42 a split) and four COVERAGE kinds: `range_filter` (several
  criteria on one range, "<>" alone), `or_criteria` (a sum of -IFS forms), and
  `conditional_sumproduct` and `nested_logic` (IF over OR, AND and NOT); file 11 says how
  each converts. Eleven Hive mappings of such conditions in `tests/test_conversions.py`, each
  Toolbox code giving the original's rows, found one gap, fixed: `COUNT(CASE WHEN c THEN 1
  END) OVER (...)`, COUNTIFS over its own Table, stayed Hive, and now converts to
  `count_rows(where=c, over=...)`.
- **--cells.** The loop's message and the runner's docstring and usage line say each run
  starts with nothing defined.
- **check_key on a partitioned table.** check_references checks it on the last Partition
  SHOW PARTITIONS lists, sorted as the compare sorts them, and prints the call for another; its
  text cell says so. The README's check step says how, with if/then.
- **compare.md.** One result for each Partition compared, under a `## ` heading; a result
  that compared no Partition, or one 8.1 wrote, gives way to the next compare. The convert
  step and the README say how to compare another, and that every result must pass.
- **The connection.** warehouse.py, the README and how-to 01 say where the lines go; the 8.2
  Upgrade step writes warehouse.py again where 8.0 or 8.1 left it, and check_references.ipynb,
  which the user's ask needs written again, as 8.0's step did for its admin notebooks.

Everything tested again, from main as b74f1a0 left it (`.scratch/copilot-eval/results.md`,
`.scratch/usability-loop/results.md`, "The ticket 19 round"): the Copilot evaluation 100% of
26 on dev and 100% of 13 held out; the Excel evaluation 100% of 42 on dev and 100% of 42 held
out, the new range and condition tasks among them; the usability loop every dev scenario 3/3
and each held-out one 1/1, its questions the conversion each Excel run asks for and H2's on
the tables an Upgrade's Databases leave named before. The loop broke a Project's warehouse.py
it brought in, 8.2's comment naming the line it replaces: fixed after the round, the comment
reworded and the loop replacing the code line alone, tested.

## Review

- Spec: the runner's usage line, the generic refusal, the AND( match narrowed to where a value
  starts, and tests for a pre-8.2 compare.md and a failed Partition beside a passing one:
  fixed. The count conversion, the range tasks and file 11's range lines answer the user's
  mid-work ask; check_references written again by the Upgrade follows from its change.
- Standards: names (partition_names, compared_on, compared_times, _results_kept,
  _check_hive_sqlglot_can_read), loops for the nested comprehension and next(...), no `or []`,
  one compared_times and one count_rows_where, if/then wording, the upgrade test split:
  fixed. Left: BatchStatement.note carrying UNREAD as a prefix, a judgement call.
- Beginner reader: `.scratch/toolbox-8-2/reports/19-beginner-reader.md`. Its three costliest
  stops are fixed: check_references' text, the refusal's file and line, and compare.md's
  docstring and done-when; the connection lines' place, file 11's OR brackets and SUMPRODUCT
  `+` too.
