# Ticket 06: beginner reader's report (2026-10-31)

Read as a Python-first SQL beginner. A beginner learns that SET lines no longer need sending by
hand: CHANGES.md 8.1, how-to 9 and the converted write()'s docstring say it plainly.

Stops, and what was done:

1. Stuck: run_tables' docstring said Session settings are "refused before anything is sent",
   then that a table's are sent. Done: settings in write() are refused, "which belong in the
   logic's session_settings()".
2. Reread: sent before every write, or once? Done: "before its first write, and again before a
   later one when another table's write came between".
3. Reread: how-to 9 lost the line saying hive.exec.parallel makes Hive faster and changes no
   row. Done: put back in the write step's sentence. (The "dynamic_partitions" setting sent by
   hand before seed() is 8.0's, for seed(), which run_tables doesn't send.)
4. Moment: session_settings()'s docstring, "sent first". Done: "sent before its query".
5. Moment: the ${...} finding's "with none, send one with hive_settings(...)": left; it is
   about a variable no SET line fills, which only the user can send.
6. Moment: CHANGES.md's "being built on dev": left, as 8.0's section said while it was built;
   the raise (13) replaces it.

Not checked by the reader: a Project made before this change keeps its old checklist box; 13's
Upgrade step deals with 8.0's checklists.
