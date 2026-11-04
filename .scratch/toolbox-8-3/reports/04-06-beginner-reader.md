# Beginner reader: tickets 04 and 06 (2026-11-04, run after 8.3's export)

Run on the newest Opus, in scratch Projects: write_decisions given each kind of answer that
matches nothing, and the convert notebook's PARTITION and step 7. 17 stops, none fixed yet.

Ticket 04, write_decisions' refusal:
1. Its docstring's sentence on the refusal is a list in a list, at the end of a long paragraph,
   right after "named": give it a paragraph and an example.
2. The fix says "by the names project.check() writes, then run this step again", but check()
   may name none, and write_decisions is called outside a step: point at the nearest names.
3. "the nearest being key" reads as a term: "did you mean key?".
4. A column with no close match gets no list of the table's columns.
5. A tag for a table that holds none: say it holds no Script tag.
6. An upper-case table name gets no nearest name: compare in lower case.
7. A "types" that isn't a dict is dropped without a word, though `_unmatched_answers`' docstring
   says answered_text names it; "tags" is named.
8. A real column whose type wasn't guessed: "is no type the Toolbox guessed" reads as calling
   the column a type, and the note-or-refusal split isn't in the docstring.
9. "1 answer ... matches" counts one mistake where the table's entry held several answers.

Ticket 06, PARTITION and step 7:
10. Step 2 teaches a bare tag's own quotes; PARTITION's value takes none, `{"dt": "'2026-09-23'"}`
    passes unrefused and fails the table: say so, and refuse a quoted value.
11. Step 7 doesn't say the dev table must hold the Partition, nor that comparing it again
    replaces a failed result.
12. "set PARTITION ... and run this step again": the names cell must be run, not only saved.
13. The compare's own report still says "give compare_batch partition=...", not PARTITION.
14. The comment's "another" and "both tables" mean nothing before step 7.
15. A plain string, `PARTITION = "2026-09-23"`, is passed over without a word.
16. "dt being the table's partition column": which table, in a batch of several.
17. Once a batch is finished, the last cell compares nothing more, which the notebook doesn't say.

Costliest: 10, 11, 7; then 13 and 6.

## Done (2026-11-04, after the user chose to fix all and re-export)

- 1: write_decisions' docstring gives the refusal its own paragraph, with an example line.
- 2: the fix says to correct each "by the name each line says it meant", then run
  project.write_decisions(DECISIONS) again.
- 3, 6: the nearest name is asked, "; did you mean key?", found with case set aside.
- 4, 5: a column or tag with no close match lists the table's columns or tags; a tag for a
  table with none says it holds no Script tag.
- 7: a "types" or "tags" that isn't a dict is refused, named with the shape to give.
- 8: "types: status's type wasn't a guess: <reference> gives it already"; the docstring
  names the case.
- 9: "N mistakes in the decisions cell, each an answer that matches no Decision".
- 10, 15: compare_batch refuses a partition that isn't a dict, or whose value is in quotes of
  its own; the runner passes PARTITION as given, so it refuses there too.
- 11, 12, 16, 17: step 7 says the dev table must hold the Partition, to run the names cell,
  which tables it compares on it, that a failed result is replaced when compared again, and
  that once the batch is finished this step's cell still compares.
- 13: the compare's hint names PARTITION and step 7.
- 14: PARTITION's comment: "a Partition for step 7 to compare besides the latest, ... its value
  with no quotes of its own: None compares only the latest Partition your dev table and its
  original both hold".

Code review of the fixes (review-standards, with the spec, on sonnet): fixed, a test of the
runner stopping at step 7 on a quoted PARTITION; the refusal split into
`_refuse_a_partition_not_a_dict` and `_refuse_a_partition_in_quotes`, double quotes caught
too; compare_batch's docstring names both refusals; a "tags" that isn't a dict refused in one
place, write_decisions, and tested; `_unmatched_kinds` keyed by decisions.ANSWERS;
`table_tags`, and "holds no Script tag, so none can be answered"; step 7's finished-batch
sentence its own. Answered: a dry run names what it would read and checks no PARTITION, as it
checks no other input; the live run refuses it at step 7.
