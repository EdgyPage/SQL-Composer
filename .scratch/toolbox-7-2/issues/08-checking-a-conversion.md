# Checking a Conversion

Type: task
Status: open
Blocked by: 07
Size: M

## Question

The user (2026-10-26): "give me the tools to check the conversions because it'll likely be the
case that something 80% convertable exists". Two checks, grilled the same day: the Hive,
compared at every Conversion (ticket 06's round trip), and the rows, through the user's `query`,
when they ask, and again after every edit they make to the converted notebook.

## Done when

- `compare_with_original(statement, original, query=query, where=...)` sends one query through
  `query` that counts the rows each gives and the rows found in one and not the other, matched
  on every column, and gives back a Verdict-like report: the counts, and a few differing rows of
  each side to look at. It reads only through `query`, never `execute`.
- A partitioned table read without `where=` is refused as any unbounded read is, unless
  `reads_all_partitions=True`; the report says which partitions it compared.
- A Statement holding Unchecked pieces is compared as any other; the report names them, since a
  difference there can't be traced further by the Toolbox.
- `compare_hive(statement, original)` gives back whether the two match once normalised by
  sqlglot, and where they first differ: the check ticket 06 runs, for the user to run again
  after editing the notebook.
- The converted notebook has a cell for each, after the logic, and `finish_conversion` keeps
  them in the Table notebook until the user removes them.
- Names are public, typed, with a Worked example on the Example database opening each
  docstring.
- CLAUDE.md's Definition of done, the beginner reader included.
