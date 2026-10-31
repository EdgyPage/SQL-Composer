# The Key, proposed from the logic and checked in dev

Type: task
Status: open
Blocked by: 03
Size: M

## Question

The Toolbox already works a Statement's Key out of its clauses (`keys.py`, ADR 0005); a
Saved table's Key is still typed by hand (map, "The Key, proposed": Q4).

## Done when

- The Key Decision's proposal for a table with logic is the Key `keys.py` works out of its
  write(): the first, with any other named beside it; None, said as found none, when it finds
  none, such as with rollup or a UNION_ALL.
- Tests for each case the map lists: several GROUP_BY columns, one not returned, a column WHERE
  holds to one value, a column another decides, rollup, a UNION_ALL stack, a nested grouping,
  and a row_number Key.
- After a table's write in dev and before its compare, `check_key` confirms the Key against the
  dev copy; a Key the rows break fails that step, naming the rows, and the runner stops there.
- Its journeys show it (`tests/test_workflow_journeys.py`, ticket 01): the Key comes from the
  proposal in every journey but references', whose tables have no logic.
