# One batch per script

Type: task
Status: open
Blocked by: 03
Size: M

## Question

"I am open to designing batch designs and lists for simple, unrelated conversions." (map,
"The names cell").

## Done when

- convert's names cell has **EACH_SCRIPT_ITS_OWN_BATCH**, False by default. True, each file of
  FILES is a batch of its own, named for its file without `.hql`, each with its own folder and
  batch.md, as if converted one at a time; NAME is unused, and its comment says so.
- One decisions cell answers every batch's tables, keyed by table; `"all_tables"` spans them.
- `project.run_workflow` runs each batch in turn, stopping at the first Decision any leaves
  open, and its report names each batch's state.
- Refused before anything is written: two scripts whose tables read each other's, naming the
  pair and saying to convert them as one batch; two files of one name.
- A journey converts three unrelated scripts so, to finished.

## Answer
