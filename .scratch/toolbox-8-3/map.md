# Toolbox 8.3: Script tags as Decisions, and a convert notebook that keeps you in it

Label: wayfinder:map

The user (2026-11-04), with 8.2 exported to main: "I hit a snag in converting sql code to the
sql composer. The code that didn't convert was unchecked sql from something under the schema
<PARM="PARMVARNAME"/>. This is a very common pattern in my conversions and I want to be able to
check for this in the convert step of the relevant workflows. I want to catch these in the
convert step sooner so it doesn't cause downstream stops in running and filling out tables. I
want to not have to fix anything past the conversion notebook so I can be assured I don't have
to bounce around the workflow steps or file structure." Grilled the same day, 25 questions,
every one settled. Partway through: "also, go through the workflow and make sure the convert
steps don't require me to make too many cells in the convert steps", which added Q22 and Q24.
The user named the version 8.3.

## Notes

### What a Script tag does to a Conversion today (2026-11-04, 8.2 at 1db77d4)

"Schema" in the user's words is the tag's shape, `<PARM="NAME"/>`, not a Database. Their real
one: `<PARM="PERIOD_END"/>`, a value the program they copy from filled in before Hive read it.

- **A bare tag**, `WHERE dt <= <PARM="PERIOD_END"/>`, stops sqlglot's tokenizer at the `<`
  ("Expected table name but got <Token token_type: TokenType.LT ..."). `_read_statement` makes
  the whole statement OTHER, an Unchecked statement: the Batch never learns the table it writes
  or what it reads, so no Saved table, Key or Lineage comes of it, and the miss shows only at
  create, seed or write. This is the user's snag.
- **A quoted tag**, `'<PARM="PERIOD_END"/>'`, reads as a string literal and converts, then
  reaches the warehouse as written, so the write or the compare goes wrong.
- `decisions.PLACEHOLDER_WORD`, `<[A-Z][A-Z_]*>`, doesn't match a tag, so no Decision catches
  it either.
- What already exists and is used: `${...}` kept as written and noted
  (`_Converter.note_variables`), SET lines kept as Session settings, the decisions cell and
  `write_decisions` (8.1), and the names cell's per-batch inputs (`RENAME`, `STAGING`).

### Script tags are Decisions (Q1-Q13, Q17-Q21)

- **One shape, any name** (Q2): exactly `<PARM="NAME"/>`, where NAME is whatever variable name
  the program used. The user (2026-11-04): "be sure the requirements match that the parms will
  be <PARM="whatever the var name is"/>, the PERIOD_END is just an exampe". So nothing is
  special about `PERIOD_END` or any other name: NAME is any text between the quotes, read as
  written (its case kept), and it is the tag's key under `"tags"`. Any other text starting
  `<PARM` stops step 1, naming its script and line, so a new shape is never quietly left in.
- **Per table, never global** (Q4): "different tables assume different dates across the program
  I'm copying from. the parms are not global variables across all statements." So no Project
  file of tags (the Tag sheet, proposed and dropped) and no names-cell `TAGS` input (Q10,
  replaced by Q17).
- **Step 1 reads past each tag, where a value goes** (Q17, Q19): the Conversion reads the
  statement with a stand-in in the tag's place, converts it as it would any statement, and
  leaves the tag an open Decision of the table it ends up in. Step 1 doesn't stop on a tag
  (this replaces Q5's "stop"). A tag where a table name, a column name or a whole condition goes
  can't be read as a value: that, alone, stops step 1, naming the line.
- **Answered in the decisions cell, under `"tags"`** (Q17), beside the table's location, Key
  and types:
  `DECISIONS = {"mart_dev.daily_close_mart": {"tags": {"PERIOD_END": "'2026-10-31'"}}}`.
  The same tag twice in one table, or in two statements writing it, is one Decision.
- **Keyed by the dev name, as `project.check()` writes it** (Q18), as every Decision is. A
  folded staging table's tags are Decisions of each table it is folded into, since it has no
  Table folder of its own (replaces Q12 and Q13).
- **The answer is Hive text, put exactly where the tag's characters were** (Q7, Q11): nothing
  added or removed, so a bare tag's answer brings its quotes (`'2026-10-31'`) and a quoted
  tag's doesn't (`2026-10-31`). An answer may be `${hivevar:period_end}`, which the existing
  `${...}` handling takes from there: one mechanism, no second kind of tag.
- **The answer lives in the Table reference** (Q20): a `tags={...}` line its logic reads, open
  while a tag in it is unanswered, as every Decision is a line of the Table reference.
- **Answering again overwrites** (Q21): a tag's written value is changed by a new answer in the
  decisions cell and step 3 run again, as a Key marked `# proposed` is today. A compare that
  fails on a wrong date means changing `DECISIONS` and running steps 3, 6 and 7 again, never a
  file edited by hand.
- **Create waits** (Q5, Q17): step 4 doesn't run while any tag is open, so nothing
  half-converted reaches the warehouse, and everything is fixed in the convert notebook.
- **What is kept** (Q8): the Conversion folder keeps each script as given, its tags in it; each
  table's scan notes each tag ("`<PARM="PERIOD_END"/>` at daily.hql:14, answered in the
  decisions cell"). A note, not a `# CONVERSION:` mark.
- **Where** (Q9): every Conversion, the convert Workflow's step 1 and new_table's step
  converting a query from `QUERIES`. Not Unchecked text the user writes by hand: tags come only
  from someone else's scripts.
- **Nothing else changes** (Q6): "I want to only take care of the parms under the schema I
  specified, the other conversions and assumptions so far are fine."

### The convert notebook without cells of your own (the user's ask, Q22-Q24)

The convert notebook ships a cell for every step, but two places sent the user out of it:

- **Step 2 has no cell**: the names to answer by come from `project.check()`, run in a cell
  the user makes, or from each table's `conversion/checklist.md`; both list Decisions as lines,
  not as code. So (Q22) **step 1's output and `project.check()` print the open Decisions as a
  whole `DECISIONS = {...}` to paste**, each value still to give `"<FILL IN>"`, with a tag's
  script and line beside it, in every Workflow with a decisions cell. A `"<FILL IN>"` pasted
  and not filled in is no answer. The Toolbox still never writes into the notebook (8.1's 02).
- **Step 7 says "in a new cell"** to compare another Partition. So (Q24) a names-cell input,
  `PARTITION = None`, which step 7's cell passes on: set it, run step 7 again.
- **Mistakes are flagged** (Q15, Q23): step 3 refuses, writing nothing, and names each answer
  that matches no Decision of the batch: a tag that isn't in the table (`PERIOD_ED`), a table
  that isn't in the batch.

### The batch that hit it (Q25)

Converted before 8.3, its tagged table is an Unchecked statement, and the Upgrade doesn't mend
it. The user converts that batch again under a new name once 8.3 is in, and drops the old dev
table once the new one's compare passes. No repair step.

### The version

8.3, the user's number (Q16), raised by the last ticket with its Upgrade step: a Project's
convert notebook gains `PARTITION` and step 7's new cell; `tests/upgrade_from/8.2/` freezes the
Example projects as 8.2 left them. Never raised by hand before that ticket.

### Words

- **Script tag**, in CONTEXT.md since the grilling (2026-11-04), and **Decision** names a
  Script tag's value among its kinds. _Avoid_ "parameter": the glossary keeps it off Session
  setting.

## Tickets

- [01 A journey through Script tags, and the hand edits it needs today](issues/01-script-tag-journey.md)
- [02 Reading past a Script tag](issues/02-reading-past-a-script-tag.md)
- [03 The tag Decision: answered, written in, answered again](issues/03-the-tag-decision.md)
- [04 Step 3 names an answer that matches nothing](issues/04-an-answer-that-matches-nothing.md)
- [05 Decisions printed to paste](issues/05-decisions-printed-to-paste.md)
- [06 PARTITION in the convert notebook's names cell](issues/06-partition-in-the-names-cell.md)
- [07 The docs and the Copilot files](issues/07-the-docs.md)
- [08 8.3: the Upgrade step and the raise](issues/08-eight-point-three.md)

One at a time, by number, the user's habit. The real dependencies are in each ticket's
`Blocked by:`.

## Records this changes

- `sqlglot_composer/`: `converting.py` (02), `decisions.py` and `workflows.py` (03 to 06),
  `upgrades.py` and `version.txt` (08).
- `tests/journeys/test_workflow_journeys.py` and its `KNOWN_FIDDLING` (01, shrinking after).
- CONTEXT.md: Script tag and Decision (already, 2026-11-04).
- CLAUDE.md: this map (with the map); 8.3 (08). CHANGES.md's `## 8.3` (02 onward).
- `docs/workflows.md`, the README, how-tos 09 and 29, Copilot files 07 and 13 (07).

## Decisions so far

- [02 Reading past a Script tag](issues/02-reading-past-a-script-tag.md): a bare tag is read as
  a name in backticks; its place in the logic is `script_tag(TAGS["NAME"])`, a new public
  name, and a quoted one's `TAGS["NAME"]` spliced into its string; TAGS lives in the Table
  reference; one name both bare and quoted in one table is refused.
- [03 The tag Decision](issues/03-the-tag-decision.md): a fifth kind, "tag", a line of TAGS open
  while it holds the tag itself, answered under `"tags"` and written again on a new answer; a
  `${hivevar:...}` answer's value comes from a SET hivevar line of the scripts, kept as the
  table's Session settings, and write_decisions says when none sets it.

## Not yet specified

- Whether the usability loop gains a convert scenario with Script tags: the user's call, asked
  at 07.

## Out of scope

- A Project-wide list of tags, or one names-cell input of them (Q4, Q10).
- Any other change to how a Conversion reads or what it assumes (Q6).
- Tags in Unchecked text the user writes by hand (Q9).
- Mending a batch converted before 8.3 (Q25).
