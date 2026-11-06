# A Script tag in PARTITION, and W7's friction

Type: task
Status: resolved
Blocked by: 14
Size: S

## Question

The user (2026-11-05), after ticket 14's round: "Fix it and the open issue from ticket 12". It
is W7's friction (results.md, "The ticket 14 round") and the gap ticket 12 found: a Script tag
in a PARTITION, `PARTITION (dt=<PARM="RUN_DAY"/>)`, stops project.convert ("its PARTITION gives
dt the value ..., not a plain one"), so a nightly script whose Partition is tagged can't be
converted.

## Notes

Checked against the code (dev at 6b403edf):

- **A bare tag in PARTITION is refused** in `converting._note_insert`, which takes a literal
  alone: `_python_of_literal` gives None for the tag, read as a name in backticks.
- **A quoted tag in PARTITION converts**, `partition={"dt": tag_text(TAGS["RUN_DAY"])}`, but a
  tag found only there is in no TAGS: `note_tags` reads the query, not the INSERT, so TAGS has
  no line for it, no Decision asks for it, and write() reads a TAGS entry that isn't there.
- **partition= refuses a Column** (`tables._partition_literal`): a Script tag's value is one,
  `script_tag(...)` giving a Column built of values, as `script_tags.is_built_of_values` holds.

So:

- **partition= takes a value built of values**: `script_tag(TAGS["RUN_DAY"])`, or
  `run_value(...)`, names one Partition, its Hive as it stands; a column that reads a table is
  refused as before. A Run value there is drawn in the lineage, an arrow into the partition
  column it fills.
- **A bare tag in PARTITION converts** to `partition={"dt": script_tag(TAGS["RUN_DAY"])}`, as a
  bare tag anywhere else does, and a tag in PARTITION, bare or quoted, is a tag of its table: a
  line of TAGS, a finding at its line, and a Decision.
- **W7's friction, in the docs**, which keep the edge cases (ticket 14): the README's convert
  steps show a Run value's file whole, its imports and register; how-to 09 says the Table
  reference a Run value imports comes first, and that a seed limit's first write adds the
  window's days the seed left out; the names cell says RENAME is how a copy keeps the
  original's name.

## Done when

- A bare tag in PARTITION converts, its TAGS line bare, and a quoted one found only there has
  its TAGS line too; each is a finding and a Decision.
- `INSERT_OVERWRITE(t, partition={"dt": script_tag(...)})` writes `PARTITION (dt='...')`, a
  Run value there is drawn in the lineage, and a column reading a table is still refused.
- A journey converts a batch whose PARTITION is tagged, answers it with a Run value, writes and
  compares.
- How-to 09 no longer says a tag in PARTITION can't be converted, and the W7 friction above is
  mended in the docs.
- `.venv/Scripts/python -m pytest` passes, the code-review skill has run, and no drift item is
  open.

## Answer
Built 2026-11-05.

- **partition= takes a value built of values** (`tables._partition_literal`): a Column
  `script_tags.is_built_of_values` holds to, `script_tag(...)` or `run_value(...)`, is written as
  its tree; a column reading a table, or None, is refused as before. INSERT_OVERWRITE,
  INSERT_INTO and compute_statistics share it, so each hint names `Column`; INSERT_OVERWRITE's
  docstring says so, which INSERT_INTO's points to.
- **Lineage** (`lineage._add_write`): each Run value a partition value is gets an arrow into the
  partition column's box.
- **Convert** (`converting._note_insert`, `convert_query`): a bare tag in PARTITION is
  `script_tag(TAGS["NAME"])`, and write() imports script_tag; the INSERT's target is read by
  `note_tags` too, so a tag found only in PARTITION, bare or quoted, has its TAGS line, its
  finding and its Decision.
- **Docs**: how-to 09's step 8 says a tagged PARTITION converts, and that the Table reference a
  Run value imports comes first; its seed limits say a write's window may add a day the seed
  left out; a Common mistake on a copy's name and RENAME. The README's Run value bullet shows
  the file whole and the Table reference first. CHANGES.md's 8.4 notes have a bullet.
- **Tests**: `tests/test_script_tags.py` (bare in PARTITION; a tag only there, bare and quoted),
  `tests/test_run_values.py` (script_tag and run_value in partition=, the lineage arrow, the
  refusal for INSERT_OVERWRITE and INSERT_INTO), and the journey
  `test_convert_a_batch_whose_partition_is_a_tag_answered_by_a_run_value`.

## Review

The code-review skill, on `git diff HEAD` with this ticket as its spec, Standards and Spec on
Sonnet.

- Standards: `_write_body` read its import from generated text (`"script_tag(" in values`):
  fixed, each value's start read, the list named `tag_imports`. `convert_query` unwrapped the
  INSERT's target as `_note_insert` does: fixed, `note_tags` reads `query.this` itself. The
  three hints repeat the union: the Type hints rule bars an alias. compute_statistics' line
  was past 96: wrapped.
- Spec: no test asked for the Decision: the test now holds the TAGS line keeping the tag
  itself, which is the open Decision `decisions.TAG_LINE` reads. run_value in partition= and
  INSERT_INTO's refusal untested: both added. `named[column]` in lineage can't miss, as tree
  and values come from one `partitioned_by` in `partitions_named`; the tree flows on as a
  literal's does (Keys and the static label read `values`, its Hive). The README and how-to
  09 use different tables on purpose, each its own story's.

The beginner reader ran on the changed docs: [its report](../reports/15-beginner-reader.md),
each of its seven stops mended.
