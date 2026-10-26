# first_match and mapped

Type: task
Status: open
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
