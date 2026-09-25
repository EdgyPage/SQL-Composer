# How much may a Statement touch and return by default?

Type: grilling
Status: open
Blocked by: 02, 03

## Question

The user's rule: a naive `select * from table` must not pull a whole table and choke the notebook
or the server. Find where this matters and make the safe behaviour the default. With the Hive
research and the API's real behaviour in hand, decide:

- when a partition filter is required, and what the opt-out looks like in code;
- whether previews get an automatic `LIMIT`;
- how results come back into pandas in chunks - partition by partition, by key range, or through
  the API's own paging - and what a chunk-at-a-time Python transform looks like;
- whether a long backfill is emitted as a series of partition-bounded Statements;
- what the Toolbox does itself, and what it leaves to the API wrapper the user already has.
