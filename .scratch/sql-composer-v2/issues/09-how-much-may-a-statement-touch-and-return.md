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

## Comments

**From "Which guardrails on how a Statement is written earn their place?" (2026-09-25).** This ticket takes five of the Hive research's six defaults: a bounded partition
filter, an automatic `LIMIT`, no `ORDER BY` without `LIMIT`, no `OFFSET`, and no `*`. Cross
joins were settled there, as `CROSS_JOIN(t)`. Guards refuse, never warn, and each has an opt-out
keyword on the offending call, named for what the user accepts, with no global switch. Load limits
aren't Guards, but using the same refuse-plus-keyword shape would spare the user a second pattern to
learn.
