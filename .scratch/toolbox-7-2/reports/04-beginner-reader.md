# Beginner reader: Toolbox 7.2 ticket 04, `first_match` and `mapped`

Read 2026-10-26 after the merge (3421133), every refusal and the Worked example run. Saved by
the session (the reader writes no file). Line numbers are 3421133's.

## Stops

1. The cheat sheet's first lines: first_match's didn't say it takes (condition, value) pairs;
   mapped's said "value" twice in six words.
2. "all of them ... are one type": an int beside a float, and a date beside a string column,
   are taken; True and False work though they weren't listed.
3. mapped's example is one long line where first_match's CASE spreads over lines: on purpose?
4. "each row gets the value its column's value is the key of": a garden path, read three times.
5. A None key: the docstring pointed to first_match alone, not how to keep the dict and label
   NULL rows (both ways found by experiment: first_match with otherwise=mapped(...), and
   mapped(fill_null(...), ...)).
6. mapped's dict parameter is named values, and "The values follow first_match's rule" could
   mean either.
7. The simple CASE form, `CASE x WHEN 'a'`, was new, and nothing said it means
   `CASE WHEN x = 'a'`.
8. Refusals: "the value rows get" and "the value rows that hold it get" read as "value rows".
9. The None-key refusal was equals' WHERE message ("would match no rows"), and its fix, is_null,
   can't go in a mapped dict (the costliest: stuck).
10. The mixed-values fix ("all strings: "1" in place of 1") can't be followed when one side is a
    typed column.
11. A Condition where a value goes didn't say which pair, or whether it was otherwise=.
12. A tuple of pairs is echoed back with square brackets inside; the why doesn't say why a
    tuple, which keeps order too, is refused.
13. The wrong-type key's message quotes the key Python's way, 'one', and says "Pass a value".
14. The Worked example labels every unmatched status "still running", not only NULL; three
    patterns for NULL across the docs.
15. The Worked example: "is_in reads the list by its name", though the Hive holds the values.
16. A run of exactly 10 minutes is "short": right, since more_than is strict, but it made the
    reader check.
17. CHANGES named the Worked example by a shortened title, with no place to find it, and a
    blank line split its list.
18. Aside: if_else still gives literal's older message for a Condition given as a value.

## The three costliest

1. Labelling NULL rows in a lookup (9, 5, 14).
2. What "one type" means, and how to fix a mix (10, 2).
3. Garden-path wording in the refusals and docstring (8, 4).

## What the session did

- 1: "The value of the first (condition, value) pair that holds for a row (CASE WHEN)." and "A
  lookup: each row gets the dict's value for its column's value (CASE x WHEN)."
- 2: first_match's docstring lists True or False, and says the kinds that mix: numbers, whole or
  not; text and dates, which Hive compares as text; or True and False.
- 4, 7: mapped's docstring is reworded, says what CASE column WHEN key means, and 6 reads "The
  values are checked as first_match's are".
- 5, 9: mapped refuses a None key with its own message, whose fix is the way that keeps the
  dict, fill_null first; its docstring shows it as an example that runs.
- 8: "the value a row gets when it holds" and "the value a row holding it gets".
- 10: the fix names the kinds, and says what to do when one side is a column: make the others
  its kind, or leave otherwise= out.
- 11: the refusal names pair N's value, the value for key N, or otherwise=.
- 14, 15: the Worked example says an unknown status gets otherwise= too, and points to the
  fill_null way; "is_in takes the list kept in WATCHED_JOBS".
- 17: CHANGES gives the whole title and says it is in the Example gallery; the blank line is
  gone.
- Left: 3 (sqlglot's own layout, which spreads a long CASE); 12, 13 and 18 (the shared
  messages of literal and _written, and if_else's, beyond this ticket); 16 (true as written).
