# The Key, proposed from the logic and checked in dev

Type: task
Status: resolved
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

## Answer

Built 2026-10-31.

- **Proposed:** `project.convert` works each Key out of a converted table's query with
  `keys.statement_keys` (`project._proposed_keys`), each with the table's partition columns
  added: a write into one Partition, `PARTITION (dt='...')`, holds dt to one value, which
  keys.py leaves out, but the table keeps every Partition's rows. The Table reference gets
  `key=[...],  # proposed by project.convert from its query; if it is wrong, answer "key" in
  the decisions cell`, any other Key named after `; another:` (`decisions.PROPOSED`,
  `tables.table_reference_text(proposed=)`): a Decision made, which an answer still changes
  while the line is as convert wrote it. None found (rollup, a UNION ALL, a GROUP BY column it
  doesn't return, a query that reads itself) leaves `key=` a Decision to make. Each table's
  checklist.md notes the Key proposed and how to change it.
- **Checked:** `project.compare_batch` runs `check_key` on the dev copy, on the Partition it
  compares, once the rows match (`project._key_checked`); compare.md keeps both Verdicts. A
  Key the rows break fails the table's compare, "but its Key (run_id) repeats", the Verdict
  naming each key that repeats; whatever stops the check fails it too, as a compare's error
  does. Settled here: the check runs in the compare step, not a step of its own, since it
  reads the same rows; so "the runner stops there" is the compare step's stop (ticket 07).
- **Tests:** test_batches' `test_the_key_proposed_for_each_case`, one per case the map lists
  (several GROUP BY columns, one not returned, a column WHERE holds to one value, a column
  another decides, rollup, a UNION ALL, a nested grouping, a row_number Key named beside the
  first), plus the proposal, none, and the decisions cell changing it; test_compare_step's (a
  Key the rows break, one they keep).
- **Journeys:** the convert journeys answer only each table's location: the Key is the
  proposal, asserted in the reference. new_table's journey still fills its Key by hand: ticket
  08 writes its Table reference from its logic, and so its proposal; references' tables have no
  logic.
- **Code review:** Standards: the rebound `verdict` (fixed: both kept), the Key check pulled out
  of `_compare_one` (`_key_checked`, which also replaces `_on_partition`), the line found by
  `startswith` (now one `re.sub` of the template's line), "proposed" not in the glossary
  (CONTEXT.md's Key says it). Spec: the map's cases untested (added), the second Key not named
  (named after `; another:`), the journeys typing the Key (they take the proposal now),
  `check_key` outside the compare's try (caught).
- **Beginner reader:** [04-beginner-reader.md](../reports/04-beginner-reader.md); its stops and
  what was done for each are there. It found the partition column left out of the proposal.
