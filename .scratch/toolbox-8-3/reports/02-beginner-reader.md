# Beginner reader: ticket 02, reading past a Script tag (2026-11-04)

Run on the newest Opus, on `script_tag`'s docstring, the refusals a beginner meets, the TAGS
block, the scan line and CHANGES.md's `## 8.3`, with a real batch run in a scratch Project.
19 stops; what was done with each:

| # | Where | The stop | Done |
|---|---|---|---|
| 1 | script_tag docstring | "returned as a Column" read as a table's column | says a Column is the type any value has, with an example |
| 2 | its example | `"'2026-09-24'"`'s inner quotes looked like a typo | comment on the line: the Hive, quotes and all |
| 3 | "`text` is always the table's TAGS entry" | why an argument, then? | "you give it the table's TAGS entry" |
| 4 | `${hivevar:period_end}` | never seen one | "a Hive variable your warehouse fills in when the query runs" |
| 5 | "Until a tag is answered" | how? and a quoted tag runs, matching nothing | says to write it in TAGS; says a quoted tag runs but matches nothing |
| 6 | "holds a partition column to a value" | jargon | says it still filters dt, a partition column, with the example |
| 7 | module docstring "a Decision" | promises the decisions cell | "which you write there"; 03 makes it a Decision |
| 8 | TAGS comment "with its quotes, if it is a string" | whose quotes? an unquoted date is subtraction | example `"'2026-09-24'"` (text or a date, in quotes) or `"5"` |
| 9 | "inside quotes: answer it with no quotes" | clear after a compare | example `"2026-09-24"` |
| 10 | TAGS_COMMENT, the checklist | can't tell whether to edit TAGS; checklist lists no tag | comment says write its value here; 03 lists tags as Decisions |
| 11 | the scan line | two colons, no bare or quoted, no comma after the script | "close.hql, line 3: <PARM="X"/>, a Script tag, bare. Write its value in TAGS, ..." |
| 12 | misshapen refusal | grammar; doesn't show the shape plainly | "has text starting <PARM that isn't a Script tag as a Conversion reads one: <PARM="NAME"/>, NAME in double quotes, closed by "/>"" |
| 13 | "where a name goes" | which name? | "where a table's name goes" or "where a column's name goes" |
| 14 | _batch_statements' fix | fits only one case | why and fix name both cases |
| 15 | bare and quoted refusal | no fix | says to write the value in place of the quoted one, then convert again |
| 16 | "it names a column, dt" | surprised | "it isn't one value: it names a column, dt" |
| 17 | CHANGES.md "a new function" | reads as the tag being the function | reworded; the bare-and-quoted refusal named |
| 18, 19 | "answered", CONTEXT.md's Script tag | promise the decisions cell (03) | wording in 02 now says to write the value in TAGS; 03 makes the glossary's words true |

Left for later tickets, as they are what those tickets build: listing tags in the checklist and
`project.check()` (03, 05); an unanswered bare tag's Hive error pointing back to TAGS (03, as
create waits while a tag is open); the convert report's "Next:" line when no table was made
(04's flagged mistakes, noted there).
