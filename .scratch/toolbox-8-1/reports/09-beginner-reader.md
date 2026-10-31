# Beginner reader: ticket 09, a new table from a query

Run 2026-10-31 on the uncommitted ticket 09 diff; saved here by the session, in short, each
stop followed by what was done.

1. **new_table's docstring never mentioned queries=.** *Done:* a paragraph: by the table's
   name without its database, Hive or a .hql file, made in DEV, what is written for you, what
   is left, what is refused.
2. **The names cell's examples didn't match; nothing said the table must be in DEV.**
   *Done:* QUERIES' example is `{"daily_job_runs": ...}` for mart_dev.daily_job_runs, and
   says it is made in your Dev Database.
3. **Step 2 "Write each table's logic ... yours" against "written for you".** *Partly done:*
   the notebook's opening says a table from a query has its logic written for you; the step
   itself is shared with tables started by hand. Ticket 12.
4. **Step 8 loops QUERIES; "batch".** Not changed: a table from a query is a batch of one, as
   the docstring says.
5. **"beside this notebook".** *Done:* "in admin/workflows/new_table/".
6. **Cell 0 never mentioned QUERIES.** *Done:* it does.
7. **File 14 says 8.0.** Not changed: the version is ticket 13's.
8. **Which Decisions a query table leaves.** Not changed: check() names each; its Key is
   proposed, its types from the tables it reads, so usually only its location.
