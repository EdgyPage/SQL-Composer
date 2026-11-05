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

## Answer
Built 2026-11-05.

- **The journey**, `test_convert_the_users_batch_with_run_values` in
  `tests/journeys/test_workflow_journeys.py`, on `PERIOD_SCRIPT`: mart.job_teams, read on
  the latest day; mart.recent_runs, a 14-day window `BETWEEN date_sub(<PARM="PERIOD_END"/>,
  14) AND <PARM="PERIOD_END"/>`, joined to job_teams, whose Key the user answers at step 3;
  and mart.team_log, partitioned by dt and team, an INSERT INTO that reads itself, so it is
  seeded. The user's function, `building_blocks/run_values.py`'s `period_end()`, gives the
  latest day through `latest_partition`, and the decisions cell, typed whole with
  `Journey.type_decisions_cell`, imports it and answers under `"all_tables"`, with a seed
  limit for team_log. It ends on the end goal: each table compared and holding its
  original's rows, each write holding the day as plain Hive, the seed copying only
  `dt >= '2026-09-24'`, and the needless `many_matches=True` gone.
- **Today** it is `xfail(strict=True)`, failing at step 1: `date_sub` converted with
  `unchecked_column("DAY")`.
- **KNOWN_FIDDLING stays `()` for convert**: writing the function is the user's own code, as
  their scripts are, and the decisions cell is typing.
- **The Example database runs date_sub and date_add**, which sqlglot's executor had no Python
  for (`engine._teach_date_add`), so the originals of the journey's scripts can be written.
- **What a Conversion writes today**, `tests/test_date_windows.py`: date_sub and date_add with
  an Unchecked DAY (02 changes it); between two Script tags bounds no Partition (03 changes
  it). `${...}` in hand-written Unchecked text is ticket 04's, built beside this one, which
  holds it in its own tests.

## Review

Code review (review-standards and review-spec, sonnet), of 01 to 03 together:

- **Fixed:** the journey asserted `date_sub('2026-09-24', 14)` in the Hive sent, which the
  Toolbox writes as `DATE_ADD('2026-09-24', 14 * -1)` (02's Answer): the assertion now says
  so. The xfail's reason names its first failure as it moves: 06's `latest_partition` once 02
  and 03 landed. The "Today" line above is what it was at 01.
- **Answered:** the unit tests for today's `between` with a tag at an end and for
  `${hivevar:...}` by hand: the first was written (`test_between_two_script_tags_...`) and
  turned to 03's behaviour when 03 landed in the same file; the second is 04's, built in its
  own worktree at the same time. `engine._teach_date_add` and `Journey.type_decisions_cell` are
  what the journey needs to run: the originals use date_sub, and the decisions cell imports a
  function. KNOWN_FIDDLING stays `()`: the function is the user's own code.
