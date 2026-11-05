# ${...} in Unchecked text is Hive

Type: task
Status: open
Blocked by: -
Size: S

## Question

`unchecked_column("... ${hivevar:run_day} ...")` is refused: `{hivevar:run_day}` reads as one
of its `{name}` placeholders, unless the braces are doubled, `${{...}}`, which the Conversion
writes and a person doesn't know to (map, Q9).

## Done when

- In every `unchecked_*` text, `${...}` is Hive, passed through as written; `{name}` is still
  a placeholder, and `{{`/`}}` still a brace.
- A `${{...}}` the Conversion wrote before 8.4 gives the same Hive as before.
- The Conversion writes `${...}` plainly from now on.
- The docstrings of the `unchecked_*` functions say it, with an example.
