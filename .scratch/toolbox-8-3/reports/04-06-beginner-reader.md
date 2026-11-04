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
