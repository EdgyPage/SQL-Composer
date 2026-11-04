# Reading past a Script tag

Type: task
Status: resolved
Blocked by: 01
Size: L

## Question

A Conversion reads each statement holding a Script tag as if a value stood in the tag's place,
and converts it as any statement (map, "Script tags are Decisions"). How a bare tag's stand-in
reads, and what Toolbox code the tag's place becomes in the logic, is settled here.

## Done when

- A Conversion finds each `<PARM="NAME"/>` in each statement, by script and line, before
  sqlglot reads it. NAME is any variable name, whatever text the quotes hold, kept as written:
  nothing is special about `PERIOD_END`, the map's example. Any other text starting `<PARM`
  refuses step 1, naming its script and line and the one shape it reads.
- Tests use several names (upper and lower case, digits, underscores), never one alone.
- Each tag where a value goes, bare or quoted, reads as a stand-in, so the statement converts:
  its table, what it reads, its Key and its Lineage are what they'd be with a value there.
- A tag where a table name, a column name or a whole condition goes refuses step 1, naming the
  line and saying a Script tag stands for a value only.
- Each table's logic keeps the tag's place so 03 can put the answer there, exactly where the
  tag's characters were. Settled here and recorded below: what Toolbox code that place is (a
  `{name}` placeholder in an Unchecked expression, a value read from the Table reference, or
  other), and how the quoted and bare cases differ in it.
- A folded staging table's tags go to each table it is folded into.
- The Conversion folder keeps each script as given, tags in it. Each table's scan notes each
  tag with its script and line.
- new_table's step converting a query from `QUERIES` does the same.
- No other conversion changes: every test of a statement with no tag passes unchanged (Q6).
- CHANGES.md's `## 8.3` begins.

## Answer
Built 2026-11-04.

- **Finding tags** (`sqlglot_composer/script_tags.py`, new): `tags_in` finds each
  `<PARM="NAME"/>` by its start, end and line, passing over comments and telling bare from
  inside quotes; NAME is any text but a quote, a backtick or a line break, its case kept. Any
  other `<PARM` as a word, in any case, outside a comment refuses step 1 naming its script and
  line (`misshapen_tag_line`); `a<parm_count`, a less-than, is no tag.
- **The stand-in** (settled here): a bare tag is read as a name in backticks,
  `` `<PARM="PERIOD_END"/>` ``, which sqlglot reads as a column (`readable_tags`), so the
  statement converts and its table, reads, Key and Lineage are as with a value; Hive written
  back from the tree has each tag bare again (`tags_as_written`). A quoted tag is part of its
  string, as sqlglot reads it.
- **Where no value goes**: a tag as a table's, a column's or an alias's name, or as a whole
  condition (WHERE, HAVING, AND/OR, NOT, ON, IF's test), refuses step 1 naming the line,
  through `project._batch_statements`, whose why and fix hold for both of its refusals.
- **The tag's place in the logic** (settled here): a bare tag's place is
  `script_tag(TAGS["NAME"])`, and a quoted one's is `TAGS["NAME"]` itself, spliced into its
  string: `'2026-<PARM="Month"/>-01'` becomes `"2026-" + TAGS["Month"] + "-01"`, so the answer
  lands exactly where the tag's characters were, with its quotes for a bare tag and without
  for a quoted one. `script_tag(text)` is a new public name, decided by this ticket: a Column
  whose Hive is `text` as written, refused when it isn't one value. A converted query defines
  TAGS inline after its imports; `saved_table_logic` moves it into the Table reference, which
  the logic imports it from (`from references.<stem> import <table>, TAGS`). Until answered,
  each entry is the tag itself, which script_tag writes in backticks and Hive refuses to run.
- **One name both bare and quoted in one table is refused**, per table: one answer can't be
  written both with its quotes and without. In a batch, that table isn't made, and batch.md
  says why.
- **A tag in a piece kept as Hive**: bare, it is a placeholder bound to
  `script_tag(TAGS["NAME"])`; inside quotes, the Unchecked text reads `TAGS["NAME"]` spliced
  in. In an IN list the list stays an Unchecked condition binding the same column, as is_in
  takes plain values only. 03 decides what an answer holding `{`, `}` or a quote does there.
- **Folded staging**: a staging table's tags are Decisions of each table it is folded into
  (`BatchStatement.folded` records what was folded in).
- **The scan** names each tag at its script's line, `close.hql line 3: <PARM="MinMins"/> is a
  Script tag: TAGS, in the Table reference, holds what it stands for, the tag itself until it
  is answered`; the script is kept as given in the Conversion folder.
- **new_table** reads a query from `QUERIES` the same way (`_refuse_a_query_it_cant_make`
  goes through `_batch_statements`), tested.
- **Q6**: every test of a statement with no tag passes unchanged. CHANGES.md's `## 8.3`
  begins.
- **Code review** (review-standards, review-spec, on sonnet). Fixed: the tag pattern in one
  place (`TAG`, `TAG_IN_BACKTICKS` built from it, `tag_pieces` for the split); backticks in
  one helper (`in_backticks`); `tags_in` one pass, no lambda; `FoundTag.end`; script_tag's
  docstring opens with what it returns; one why and fix for the batch's two refusals;
  `tag_is_quoted` for the bool; `note_tags` split from `_tags_found`; three expressions spelled
  out; `is_script_tag` for conditions.py; comparisons.py's comment. Spec: a quoted tag in an
  Unchecked piece no longer refuses; the scan's script and line; tests for new_table, an IN
  list, a function, arithmetic, a staging table folded into two tables; `<PARM` in a comment
  or a less-than is no tag. Answered: `_is_plain_value` reads sqlglot's tree and
  `is_script_tag` the Toolbox's, two trees, not one job twice. Left to 03: an answer's
  escaping in a quoted tag (spec 5); D410's wording, fixed here.
- **Beginner reader**: [its report](../reports/02-beginner-reader.md); stops 1 to 17 reworded
  here, the scan line now naming bare or quoted at "close.hql, line 3", and the refusal naming
  a table's or a column's name; the rest are what 03 and 05 build.
