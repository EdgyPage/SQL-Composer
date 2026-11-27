# check_project warns while a History table lacks its Seed's days

Type: task
Status: open
Blocked by: 05
Size: S
Spec: [specs/06-check-project-warns-of-missing-days.md](../specs/06-check-project-warns-of-missing-days.md)

## Question

A Seed that couldn't load every day goes on (ticket 05); what it left out must stay visible
(round 2, Q5; round 3, Q6).

## Done when

- **`check_project` gives a Warning**, never a refusal, for each History table that lacks
  Partitions its Seed's limit named, or holds them empty: "mart.job_day_facts lacks 3 of the
  31 days its Seed loads: 2026-10-04, ...".
- A Rebuilt table, and a History table holding every day, give none.
- **Tests**: a History table missing days, one with an empty day, and one whole.
- The beginner reader runs, since a new Warning is a message a beginner reads.
