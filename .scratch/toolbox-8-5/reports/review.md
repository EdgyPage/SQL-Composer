# Toolbox 8.5: the code review (2026-11-06)

The code-review skill on `git diff dfd5cc4d` with the map and tickets 01 to 13 as the spec,
Standards and Spec on Sonnet.

## Spec, and what was done

- **The Upgrade didn't mark a call of the user's giving `compare_batch(partition=...)`** (ticket
  04's note for 13): fixed. `upgrades.calls_to` takes `keyword=`, and `to_8_5` marks each such
  call, `compare_batch takes partitions=, a list, ...`.
- **A Run value given only in promote's decisions cell read dev's block** (ticket 10's "not
  done"): fixed. promote's write-answers step points each Run value's import in a prod
  reference at its block's prod copy, writing the copy when promote wrote none
  (`project.prod_run_values_pointed`, `_write_prod_block` shared with `_write_prod_blocks`).
  The prod reference's hash leaves out a Run value's import, as it does SEED, so check() no
  longer calls a prod reference given one "edited by hand" (an 8.4 gap too).
- **A table changed in dev and promoted again kept its prod rows** (ticket 03's "not done"):
  fixed. Its promotion record counts its prod copy's writes when promoted
  (`"writes_when_promoted"`), and promote's write step is done only with one more
  (`workflows._is_written_since_promoted`); the journey asserts the second write.
- **references places no location** (09): as decided there, a Table reference add_references
  writes is a table someone else owns, with no `location=` by design; 09's Done when meant
  the tables of yours that convert, new_table and reference_from_logic write.
- **The mark names a root only from a Table reference** (13): kept; a Saved table's location
  is in its Table reference, which is where the Upgrade reads.
- **One batch per script runs past a batch's Decision** (05): kept, so one paste answers every
  batch, the user's "simple, unrelated conversions".
- **8.4's two strings still read** (09): kept until the Upgrade writes the dicts, so a Project
  keeps working between copying in 8.5 and upgrading.
- **new_run_value run again changes nothing; a table's own "key": "proposed"; partition=
  refused**: decided in 06, 07 and 04, each for a reason its Answer gives.

## Standards, and what was done

No hard violation. Judgement calls taken: `_seed_written` is `_has_seed_written`;
`_partitions_checked` is `_partitions_to_compare`, as `check_` refuses; `with_location_placed`,
which project.py alone calls, is `_with_location_placed`. Left: project.py's size (it holds
every Project action, as `toolbox_registry` lays out the folder); the seed's answer read across
decisions and workflows (one reader, `decisions.seed_answer`, each place calls).
