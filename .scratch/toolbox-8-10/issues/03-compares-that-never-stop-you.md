# Compares that fill the user's params, and never stop the user

Type: task
Status: open
Blocked by: -
Size: M
Spec: [specs/03-compares-that-never-stop-you.md](../specs/03-compares-that-never-stop-you.md)

## Question

The convert Workflow's compare (step 7, `project.compare_batch`) sends a query alone's
`conversion/statement.hql` as written, with `<PARM="X"/>` and `${hivevar:x}` still in it, so it
can't run; and any compare that isn't a pass keeps the batch out of `finished/`, so promote
refuses it (round 1, Q3 to Q5; round 2, Q1; the map's "Compares and the user's params" note).
The user: "a promote to prod is not a Toolbox call, it's mine ... note the warnings in obvious
language, but don't stop the user."

## Done when

- **A query alone is filled before it is sent**, when every value is known: each Script tag by
  its answered Decision, each Hivevar by its default or answer, each Run value by the value
  recorded when the dev table was written, never by calling its function again. The bare tag is
  read with `readable_tags`, as `compare_hive` reads it.
- **Where a value isn't known**, that compare is skipped with a plain reason, such as "not
  compared: it holds <PARM="X"/>, which only your program fills".
- **No compare result blocks anything**: a pass, a fail or a skip, the batch reaches
  `finished/` and promote promotes.
- **Obvious warnings**: `compare.md` puts each failed and skipped table first, in plain words;
  a fail on a table with answered tags adds that the original's last run may have used other
  values; promote names each table it promotes that failed or wasn't compared.
- **Tests**: `compare_batch` on a query alone holding a bare tag, a quoted tag, a Hivevar and a
  Run value, each filled; one with an unknown value skipped with its reason; a failed compare
  and a skipped one, each reaching `finished/` and promoted with its warning. The refusals that
  are gone leave `tests/snapshot/known.txt`.
- The beginner reader runs, since what promote and `compare.md` say changes.
