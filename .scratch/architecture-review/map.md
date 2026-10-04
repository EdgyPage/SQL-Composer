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
- [One bottom read for by_day, writes and lineage](issues/02-one-bottom-read-for-by-day-writes-and-lineage.md):
  one walk down FROM; by_day follows the Date partition as a column under every name it is
  given, refuses a LIMIT, and says where a dropped Date partition goes; part of 3.2, which
  isn't exported yet.
- [Aggregate and window placement from the tree](issues/03-aggregate-and-window-placement-from-the-tree.md):
  a Column's counts and row numbers are read from its tree; one placement check; the GROUP BY
  Guard walks SELECT, HAVING and ORDER_BY; ORDER_BY names and row_number's sort keys checked;
  part of 3.2.
- [One refuse() for misuse refusals](issues/04-one-refuse-for-misuse-refusals.md): every
  no-opt-out refusal goes through refusals.refuse(); messages unchanged but one; 46 misuse
  refusals tested in four parts.
- [Warehouse answers through one module](issues/05-warehouse-answers-through-one-module.md):
  one _ask for DESCRIBE and SHOW PARTITIONS; an empty Saved table matches; arguments checked;
  file names never shadow a module; describe_text and show_partitions_text off the Edition
  interface.
- [Both Example databases refuse the same way](issues/06-both-example-databases-refuse-the-same-way.md):
  SQL Composer's adapter refuses what sqlglot can't read or run in four parts, as Spark
  Composer's does, and reads a query's tables from sqlglot's tree; send takes only Hive text.
- [Join Guards read the condition tree](issues/07-join-guards-read-the-condition-tree.md):
  LEFT_JOIN lets through a WHERE that keeps the rows with no match; a key inside a Building
  block is found.
- [Narrow the Edition seam](issues/08-narrow-the-edition-seam.md): nothing on the seam both
  Editions write the same; the writers agree on every date_sub.
- [A plain-code pass](issues/09-a-plain-code-pass.md): plain loops and data where a reader
  lands after a refusal; nothing a user sees changes.
- [The repo's own guards](issues/10-the-repos-own-guards.md): main can't be moved by hand, the
  drift review sees every new commit, and the hooks are tested as Claude Code runs them.
- [The lineage page](issues/11-the-lineage-page.md): the page stays in lineage.py; its script
  is checked by Node.

## Candidates not yet ticketed

None: under the user's goal (2026-10-03) to implement every candidate worth it, each of the 11
has a ticket, and each ticket records what it left out as not worth it, and why.

## Out of scope

- Anything ADR 0001 or ADR 0002 decided.
