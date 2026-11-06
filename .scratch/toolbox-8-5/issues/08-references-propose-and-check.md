# The references Workflow proposes and checks

Type: task
Status: resolved
Blocked by: 07
Size: M

## Question

About 8 runs stopped on a Table reference's TODO lines, and about 7 typed `check_key` lines to
choose a Key (map, Q14, Q15).

## Done when

- `add_references` writes "what one row is" proposed from the Key, "One row per run_id.",
  `# proposed`, and leaves it a TODO with no Key; and `does_not_add_up` proposed from each
  column's name and type (`avg_*`, `*_ratio`, `*_pct`, `*_rate`, a double `*_per_*`), `# proposed`.
- Its Key step proposes a Key per table, from the columns DESCRIBE gives and one count of
  distinct values per likely id column through the user's query, runs `check_key` on it, and
  prints each verdict and the DECISIONS line to accept it.
- A proposal is accepted as a Key is (07), and project.check() names a `# proposed` line left.
- Journeys: references with no `check_key` typed and no TODO line edited.

## Answer

Built 2026-11-05.

- `tables.proposed_key_from_rows(t, query)`: the id columns (`id`, `*_id`, partition columns
  aside); one SELECT counting rows and each one's distinct values on the latest Partition
  (every row with none); the first as many as the rows is proposed, then checked with
  `check_key` on the latest two Partitions; one that repeats there (a snapshot table, such as
  ops.job_owners) is proposed again with the partition columns and checked again. None,
  saying why, with no id column, no Partition, no unique id, or a Key that still repeats.
- `project.add_references` writes it (`decisions.with_proposals`). key= stays open,
  `key=None,  # TODO: proposed ["run_id"], checked: accept it in the decisions cell`, so the
  Key step still waits for the user's yes (decided: a Key read from rows is evidence, not
  proof). The first line, `"""ops.job_runs - One row per run_id."""  # proposed from its
  Key`, stays a TODO with no Key. `does_not_add_up=[...],  # proposed from its columns'
  names` (`decisions.proposed_does_not_add_up`: avg_*, *_ratio, *_pct, *_rate, a double
  *_per_*), or `[],  # proposed: no name says ...`. Its report prints each Verdict and the
  DECISIONS line that accepts: the table's own, or "all_tables" for two or more. A query that
  fails leaves the TODOs, named.
- check()'s next step offers the proposal itself as the table's "key" (`Decision.subject`
  holds it), or "all_tables": {"key": "proposed"}. A Key written while the first line is
  still the proposed one proposes that line again.
- check() names each `# proposed` line left, blocking nothing, with how to accept it.
- REFERENCES' step texts: step 1 counts and checks; step 2 pastes the proposal, how-to 21
  only for a Key of one's own; step 3 reads the proposed lines.
- Journeys: `_run_references` and `_run_references_through_the_runner` (now top to bottom)
  paste what check() prints, type no check_key, edit no TODO, and assert none is left;
  `test_references_of_many_tables_accept_every_proposed_key` takes the all_tables path.
  KNOWN_ACTIONS unchanged: its measured journeys don't run references.
- Left for ticket 11 (generated or doc files not touched here, their tests failing until
  then): the README template's and the how-tos' add_references output, the how-to and
  docs/workflows.md text the Workflow writes, the Example projects (regenerate with
  `tools/example_project.py`, updated to match and checked into a scratch folder), and
  tests/snapshot.
