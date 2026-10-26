# first_match and mapped

Type: task
Status: resolved
Blocked by: 01
Size: M

## Question

The Hive the user converts has "lots of effective if/else statements and long INs" (2026-10-26).
`if_else(condition, then, otherwise)` writes a CASE of one WHEN; nested fifteen deep it is no
easier to keep than the Hive. The user said yes to two functions for the Conversion to write, and
for the user to write themselves.

## Done when

- `first_match([(condition, value), ...], otherwise=...)` gives back a Column written as one
  `CASE WHEN ... THEN ... [WHEN ...] ELSE ... END`, the first condition that holds winning.
  `otherwise=` left out writes no ELSE, so a row matching nothing is NULL, which the docstring
  says.
- `mapped(column, {"a": "Apple", ...}, otherwise=...)` gives back a Column written as
  `CASE column WHEN 'a' THEN 'Apple' ... END`, for a lookup on one column. Keys are one type, as
  the column's; a key the column's type can't hold is refused, as `equals` refuses one.
- Both refuse an empty list or dict, values of types that don't mix, and a value that is a
  Condition where a value belongs. Lineage traces every column either reads.
- `is_in(column, NAMED_LIST)` with a list kept as a constant is shown in a Worked example, since
  that is how a Conversion writes a long IN; `is_in` itself doesn't change.
- Each name is public, typed, with a Worked example opening its docstring, and in the gallery.
- CLAUDE.md's Definition of done, the beginner reader included: the names are new and public.

## Glossary

None: these are Column functions, as `if_else` is.

## Answer

Built 2026-10-26 in a worktree beside ticket 03, for the main session to merge into dev.

- `first_match([(condition, value), ...], otherwise=...)` and `mapped(column, {key: value, ...},
  otherwise=...)` in `calculations.py`, public (names 104), each a Column. `first_match` writes
  `CASE WHEN c1 THEN v1 WHEN c2 THEN v2 ... ELSE o END`; `mapped` writes the simple CASE,
  `CASE column WHEN k1 THEN v1 ... ELSE o END`, which sqlglot writes as Hive's and reads back
  the same (to_hive's read-back check passes on it, and its pretty layout spreads a long one
  over lines, as it does a long CASE WHEN). `otherwise=` left out, or None, writes no ELSE, so a
  row nothing matches gets NULL; both docstrings say so.
- **One Node kind, not a new one.** `Case` in `trees.py` gained a `this` part, first, as
  sqlglot's Case has it: the column `mapped` looks up, each If's `this` then a key. The
  breadth-first column order matches sqlglot's (`tests/sqlglot_checks` holds it over a new
  corpus case, `calculations:case_chains`). `writing.py`'s `_case` writes `this` and ELSE only
  when present.
- **Which types mix.** The families `equals` already uses (`COMPARABLE_VALUES`): numbers
  together (an int beside a float is fine), strings, dates and timestamps together, True/False
  alone. None (NULL) and a value whose type isn't known, such as an `if_else(...)` or a
  `first_match(...)` inside, go with any. A new `tables.value_family(value)` gives a value's
  family, a Column's from its type. The values and `otherwise=` are checked together, and
  `mapped`'s keys among themselves, which matters only on a column with no type: a typed column
  checks each key through `literal(..., column=...)`, as `equals` does, with its message.
- **Refusals**, all four-part through `refuse(...)`, each in `test_misuse_refusals.py`'s table:
  an empty list or dict (ValueError); `first_match` given anything but a list (so a lone pair
  passed without its list is caught), an item that isn't a two-item tuple or list, a pair with
  no condition first, and its own message for a pair written the other way round; `mapped`
  given anything but a dict, or a Column or Condition as a key (the fix points to
  `first_match`); a Condition where a value goes, in either; values or keys whose types don't
  mix. A None key gets the Guard `equals` gives None (GuardRefused, "compares with None"), and
  the docstring says how to give NULL rows a value instead.
- **As `if_else` does:** the result carries no type, and adds up unless one of its values
  doesn't (`sum_of` refuses a CASE over an average, with the average's reason). `if_else`
  itself is unchanged, so it still meets a Condition as a value with `literal`'s "isn't a single
  value"; giving it the new message is a small follow-up if wanted.
- **Lineage** traces every column either reads (each condition's, each value's, `otherwise=`'s
  and `mapped`'s own), in the usual breadth-first order, and shows the call as written, the
  pairs or dict spelled out: the Toolbox can't see the name of a constant passed in.
- **The Worked example** is a new Statement script,
  `worked_examples/statements/named_lists_and_lookups.py` ("Keep a long list and a lookup as
  constants, and an if/else chain as one CASE"): `WATCHED_JOBS` read by `is_in(job_runs.job_id,
  WATCHED_JOBS)`, and `STATUS_LABELS` by `mapped`, beside a `first_match`; its rows are checked
  against pandas in `test_worked_example_common_jobs.py`. It and the docstrings say "hand-written
  Hive", not "Conversion", which joins the glossary with ticket 07.
- Each docstring opens with a Statement on the Example database through `to_hive`, so the
  gallery runs it. CHANGES.md's 7.2 "Also new" has the line; the README template's cheat sheet
  counts 104 names (its lines come from the docstrings); the gallery and the golden Hive
  corpus are regenerated (the how-to page came out the same). Tests:
  `tests/test_first_match_and_mapped.py`.
- Not run here, as the brief left them to the main session after the merge: the `code-review`
  skill, the beginner reader (Definition of done 4: the names are new and public) and the drift
  review.

## Reviews

Merged into dev as 3421133 (with 8d35ba6, which took out conflict markers the merge left in
CHANGES.md); review fixes in the commit after.

- Standards (2026-10-26): no hard breach. Fixed: `calculations._case`, which shared its name
  with `writing._case`, is `_case_column`; "rule", which the glossary avoids, is gone from
  mapped's docstring. Answered: the twin refusals and the `_MIXED_WHY`/`_MIXED_FIX` dicts stay,
  as the plainest form of two messages each; "lookup" and "constant" are plain English, read as
  such by the drift reviewer too; `_case_column` reads `otherwise` as the last value because it
  appended it, in the lines just above.
- Spec (2026-10-26): answered: a string beside a date mixes, as `equals` lets it, since Hive
  compares dates as text; the extra refusals (a pair the wrong way round, a tuple for the list)
  each catch a mistake the ticket's "refuses" covers. Fixed: mapped's docstring says a key
  written twice keeps its last value. The Definition of done is met here, after the merge.
- Beginner reader: [reports/04-beginner-reader.md](../reports/04-beginner-reader.md); the
  costliest stop, labelling NULL rows, fixed with mapped's own refusal and a docstring example.
- Drift: 3421133 and 8d35ba6 clean.
