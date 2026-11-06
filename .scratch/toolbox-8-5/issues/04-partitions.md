# PARTITIONS for the compare

Type: task
Status: resolved
Blocked by: 02
Size: S

## Question

About 8 runs compared another Partition from a script of their own, once the batch was
finished (map, "The names cell").

## Done when

- convert's names cell has **PARTITIONS**, a list of Partitions, each a dict as 8.4's PARTITION
  was, in place of PARTITION. The compare step compares the latest and each listed, one
  compare.md section each. Left `[]`, the latest alone, as today.
- A finished batch compares again through the same cell, no script: `compare_batch` takes
  `partitions=`, and the step runs on a batch in `finished/`, saying so.
- The Upgrade (13) carries a PARTITION given into PARTITIONS.

## Answer
Built 2026-11-05.

- convert's names cell has `PARTITIONS = []` in place of `PARTITION = None`; step 7's cell is
  `project.compare_batch(NAME, query=query, partitions=PARTITIONS)`, its action text and the
  compare.md line that names the other Partitions ("add it to PARTITIONS, such as PARTITIONS =
  [{"dt": "..."}] ...") name PARTITIONS.
- `project.compare_batch(..., partitions=)`: each table is compared on the latest Partition
  both hold, then on each listed Partition it is partitioned by, one compare.md section and
  one report line each. A listed one that is the latest is compared once; one a table isn't
  partitioned by is named in the report as left out; the latest's "N other Partitions ... not
  compared" no longer counts the listed ones. Refused: a partitions= that isn't a list (8.4's
  dict, named "not a list of Partitions"), an item not a dict, a value in quotes of its own,
  a Partition no table compared is partitioned by.
- **partition= is refused**, not kept: one way per job (two keywords for one job, and 8.4's
  meant "in place of the latest", which 8.5 no longer does, so keeping it would change what
  old code does silently). It goes through `**removed`, as 7.0's send= did, and the refusal
  names `partitions=` with the given dict in a list, or, for `partition=None` (an unupgraded
  8.4 cell), says to leave it out.
- **A finished batch compares again through the same cell**: compare_batch on a batch in
  `finished/` says "The batch was finished already, in admin/workflows/convert/finished/<name>/:
  it stays there", and `project.run_workflow` (both run cells) runs step 7 alone on a finished
  batch whenever PARTITIONS lists a Partition (`workflows.is_compared_again`), headed
  "7. Compare each table with its original, again, on each Partition PARTITIONS lists"; with
  PARTITIONS empty it is "every step is done", as before. `batch_instances` now reads finished
  batches' records too, so step 7's done check reads their tables; `instances_of` still passes
  them over. It re-reads each time it is run: no file says a listed Partition was compared for
  a table not partitioned by it.
- `tools/copilot_eval_tasks.py`'s convert reference answer passes partitions=PARTITIONS, so it
  still runs.
- Tests: `tests/test_compare_step.py` (latest and listed, a section each; [] the latest alone;
  a listed latest once; partition= refused naming partitions=; a finished batch compared again,
  saying so; the 8.4 tests moved to partitions=); journeys: PARTITIONS step by step and through
  the runner, and a finished batch compared again through "Run the rest". KNOWN_ACTIONS
  unchanged: neither measured journey compares another Partition.
- **For the Upgrade (13)**: in a convert notebook's names cell, turn `PARTITION = None` into
  `PARTITIONS = []` and `PARTITION = {...}` into `PARTITIONS = [{...}]`, keeping the value
  given; step 7's cell `partition=PARTITION` becomes `partitions=PARTITIONS` (the notebook
  rewrite in the new order covers it); mark with an UPGRADE line any other call of the user's
  passing `compare_batch(..., partition=...)`, which is now refused. 8.4's own step
  (`upgrades.py`, around its `PARTITION` note) is left as it is.
- Left to 11: `docs/workflows.md`, how-to 29, `docs/clean-branch-readme.md`, the Copilot
  sources and files, the Example projects and the snapshot still say PARTITION / partition=.
