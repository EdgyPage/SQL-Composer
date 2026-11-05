# A journey through the user's batch, and what it needs today

Type: task
Status: open
Blocked by: -
Size: M

## Question

Before anything changes, run the user's batch as they ran it: the convert notebook, top to
bottom, on scripts shaped like theirs (map, "What the user hit").

## Done when

- `tests/journeys/test_workflow_journeys.py` gains a convert journey, run as the others are
  (the notebook the Project ships, the Example database's `query` and `execute`), whose
  scripts hold:
  - a table reading a partitioned table through windows such as
    `dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 14) AND <PARM="PERIOD_END"/>` and
    `date_sub(<PARM="PERIOD_END"/>, 7)`;
  - a table whose write reads itself, so it is seeded, over a table of several Partitions,
    partitioned by a date and by a column that isn't one;
  - a join on a table whose Key is open at step 1 and answered at step 3.
- It ends on the convert Workflow's end goal, each table written in dev and compared with its
  original, `PERIOD_END` answered by a function of the Project's giving the latest Partition,
  and the seed limited to the Partitions the table needs.
- Every hand edit it needs today is a named step in `KNOWN_FIDDLING`. What can't be done today
  (a Run value, a seed limit) makes it `xfail(strict=True)`, naming the first failure, until
  the ticket that mends it lands.
- A unit test per shape holds what the Conversion writes today, for 02 to 04 to change:
  `date_sub` and `date_add`, `between` with a tag or a calculation at an end, and
  `${hivevar:...}` written by hand in `unchecked_column`.
