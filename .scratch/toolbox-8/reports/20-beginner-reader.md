# Ticket 20: beginner reader's report (2026-10-31)

Read as a Python-first SQL beginner with a 7.2 Project, one Conversion open in
admin/conversions/team_runs/. Advisory only. Each stop, what it cost, and what was done.

## CHANGES.md, ## 8.0

- Opening, "from a new table to someone else's Hive ... and on to": read as one journey, not a
  range of jobs, with no hint that `finish_conversion` is gone. Done: "such as a new table, a
  Conversion ..., or a Promotion", and a sentence saying `finish_conversion` is gone.
- "Run `project.upgrade()`" skipped copying in the new folder first. Done: "Copy in 8.0's
  `sqlglot_composer` folder, as the README's Update says, then run ...".
- "Two files of one name are refused": a folder can't hold two. Done: "from different folders".
- "a query alone whose table is one the batch reads": a query alone writes no table. Done: "a
  query alone named as a table the batch reads or writes, such as `job_runs.hql` in a batch
  that reads `ops.job_runs`".
- "is converted again as a batch" read as the Upgrade doing it. Done: "is yours to convert
  again".
- "keeps its 7.2 folder, your changes to its notebook too" read as carrying the changes over.
  Done: says 8.0's convert writes the notebook afresh, so copy changes over from
  admin/removed/.
- Where `table="mart.team_runs"` goes now: stuck. Done: its own bullet, delete the line; the
  table it named is now the Prod copy: set PROD and promote it.

## What the Upgrade printed and marked

- "archived admin/conversions/team_runs/original.hql, which this version no longer has" read as
  dropped. Done: `Upgrade.retire` takes a reason; a Conversion's files say "a 7.2 Conversion's,
  which 8.0 converts as a batch".
- Neither the checklist nor check() named DEV. Done: the 8.0 step marks each name in
  admin/databases.py still `<...>`, as the ticket asked ("its names marked for the user");
  how-to 28 now shows filling them in.
- "DATABASE as you gave it in 7.2" pointed at the wrong archived file. Done: names 7.2's
  admin/convert.ipynb, kept in admin/removed/<stamp>/admin/convert.ipynb.
- The finish_conversion mark said neither delete nor what replaces it. Done: "delete this line,
  convert the Hive again in admin/workflows/convert/convert.ipynb, and promote its table for
  the name you gave here".

## The two new refusals

- Two files of one name: clear.
- The clash refusal was the costliest stop: it named a table the query never writes, gave two
  fixes that disagreed, and `rename=` provably failed. Done: its own refusal in
  `project._refuse_a_query_named_like_another`, before the batch plan: "the query alone in
  job_runs.hql is named job_runs, for its file, job_runs.hql, and so is ops.job_runs, a table
  the batch reads or writes", with one fix, "Rename job_runs.hql, such as
  job_runs_report.hql, and FILES with it", or, for a batch of one, "Name the batch otherwise".

## README Excel steps and convert's docstring

- Step 5, "named for its final Table ... or, when the batch is one file, for the batch": which
  name wins. Done: "With one file, name the batch for its final Table"; "not for a table it
  reads"; the doubled "in" and the place said three times are gone.
- convert's docstring, "a query alone whose table": Done: "a query alone named as a table the
  batch reads or writes, such as job_runs.hql in a batch that reads ops.job_runs".
- "Each is named <table>_<its database>" vs a query alone's plain name: left; the docstring
  says both.
