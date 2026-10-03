# SQL Composer: the architecture review of 3.1

Label: wayfinder:map

## Destination

Both Editions of the Toolbox refuse what would give a wrong answer, test what a beginner is
likely to hit, and read at the level of an intermediate Python user who knows a little SQL:
fewer shapes for the same job, and no idiom cleverer than it needs to be.

## Notes

- **Where it comes from.** On 2026-10-03 the user ran `/improve-codebase-architecture` on both
  Editions, asking for errors, test gaps, more compact code and code pitched at an intermediate
  Python user and an entry-level to early-mid SQL user. Seven explorers read the Toolbox, the
  tools and the tests, each followed by a second reader who tried to refute every finding and
  reproduced the bugs. All 90 findings held, some at a lower severity. They are grouped into
  the 11 candidates in [report.html](report.html), which has each one's files, problem,
  solution and before/after diagram.
- **The user's choice (2026-10-03).** Asked which candidate to explore, the user answered
  "Follow your heart", leaving the order and the decisions inside each ticket to the agent.
  The report's top recommendation, candidate 1, goes first. Decisions a ticket makes on its own
  are recorded in the ticket, so the user can overturn them.
- **Every ticket follows CLAUDE.md's Definition of done**: both runs pass, the code-review skill
  has run with the ticket as its spec, no drift item is left open, and the beginner reader has
  run when a refusal or docstring changes.
- **The version.** These tickets change what the Toolbox refuses, so the drift reviewer will
  open version items. Only the user raises TOOLBOX_VERSION; the items wait for their answer.
  Ticket 01 is 3.2 (the user's choice, 2026-10-03).

## Decisions so far

- [The days a Date partition bound reads](issues/01-the-days-a-date-partition-bound-reads.md):
  a day must be written exactly as the date_format writes it, date_format must be year first,
  and a Span gives exactly the days its conditions let through, left-out days and any_of
  included; shipped as 3.2, which the user chose.

## Candidates not yet ticketed

In the report's order, with its strength:

2. **One bottom read for by_day, writes and lineage** (Strong): by_day splits a top-N per day,
   and matches the Date partition by bare name.
3. **Aggregate and window placement from the tree** (Strong): the GROUP BY Guard's misses,
   row_number in WHERE, ORDER_BY names, the dead `_window` flag, fill_null's flag.
4. **One `refuse()` for misuse refusals** (Strong): three hand-made shapes, about 35 untested
   refusals, about 80-110 lines.
5. **Warehouse answers through one module** (Strong): the empty Saved table's advice, raw
   errors from an empty answer or a table name as text, `calendar.py`.
6. **Both Example database adapters refuse the same way** (Strong).
7. **Join Guards read the condition tree** (Worth exploring).
8. **Narrow the Edition seam** (Worth exploring).
9. **A plain-code pass for the intermediate reader** (Worth exploring).
10. **Repo guards: protect_main, the drift review, the export** (Worth exploring).
11. **Take the lineage page out of Python** (Speculative).

## Out of scope

- Anything ADR 0001 or ADR 0002 decided.
