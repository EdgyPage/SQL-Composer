# Ticket 13: the beginner reader on a batch

Run 2026-10-31 on commits 7e20352 and 062bb4a (opus). It read convert's and scan_hive's
docstrings, CHANGES.md's batch bullet, CONTEXT.md's Batch and Conversion, how-to 27's Common
mistakes, then converted two scripts of its own on the Example database: the batch worked at
the second try, the first refused until DEV was filled in. Its stops, with what was done.

| # | Where | The stop | Done |
|---|---|---|---|
| 1, 17 | convert's docstring; scan_hive's refusal | "once scan_hive has shown what it will make" for a batch; "then scan it again" | Scanning is said for one query only; the fix no longer says to scan again |
| 2, 3, 9 | convert's docstring | `name` and `files=` described for one query; one 16-line paragraph | The batch paragraph says what `name` names and that `files=` takes paths from the folder you're working in; three paragraphs |
| 4 | start()'s Next | DEV not mentioned until convert refuses | Left: the refusal says it plainly; ticket 19 brings the README's steps to it |
| 5 | rename= | a key not written as db.table silently ignored | Refused, naming it, before anything is written |
| 6 | Admin log, admin/removed/, notebook headers | Conversions and finish_conversion calls the user never made | Ticket 14: the batch writes Table folders itself |
| 7 | a CTAS's Table reference | a type neither the query nor DESCRIBE tells written "string" silently; STORED AS dropped | The report names each column to check; STORED AS is ticket 14's ("nothing a CREATE answers is a placeholder") |
| 8 | SET lines | run_tables, which Next names, doesn't send session_settings() | Ticket 14's checklist, with the settings |
| 10, 13 | scan_hive's docstring; CONTEXT.md | a clause read as a list item; "One query" read as "only one" | Left: rare readings |
| 11, 18 | CHANGES; the report's Next | run_tables refuses a dev table with no location= | Next names location=, the folder its files go in |
| 15, 16 | how-to 27; convert.ipynb | the steps and the notebook still split scripts by hand | Ticket 14 rebuilds the convert step list; ticket 19 rewrites how-to 27 as a batch |
| 19 | the report | the dev references and the scans' counts not listed | Left for ticket 14's checklist |
| 20 | original.hql | not the script as given, but the write rewritten in dev | Ticket 14: tables/<t>/conversion/ keeps the statement it came from |
| 21 | do_next after a batch | "No Workflow is started" | Ticket 14: the batch is the convert Workflow's instance |
| 22 | a batch run again | half-made Conversion folders, an empty list in the Admin log | Refused up front, naming each table already made; the log counts Saved tables |
| 23 | the clash refusal's why | doesn't say why two tables can't share a name | It says each becomes a Saved table of its own, named for it |

Stops 12 and 14 were not stops.
