# The Pivot filter Decision

Type: task
Status: open
Blocked by: 07
Size: L

## Question

Each Pivot filter's Decision and its proposals (round 1, Q6; round 3, Q4; round 4, Q2;
CONTEXT.md's Pivot filter).

## Done when

- **One Decision per Pivot filter**, in the convert notebook, answered as 8.5's Decisions are,
  its default keeping the filter as converted.
- **Its proposals:**
  - fold into the grain: the condition dropped, its column added to the GROUP BY;
  - one batch per value: the value a Run value, the table partitioned on the column;
  - a table per value, named `<pivot>_<value>`.
- **Each proposal shows how many tables it makes**: for each layer, the count of values the
  pivot cache holds, as "at least", and the layers combined, such as "Region: at least 3
  tables; Site: at least 100; Region and Site: at least 300". The text says a handful is
  manageable and a hundred is a reason to fold or batch.
- Answering it again changes it, as every Decision does; promotion waits on it as on any.
- Tests: each proposal gives the table it says, on the Example database; the counts from a
  fixture with two layers.
