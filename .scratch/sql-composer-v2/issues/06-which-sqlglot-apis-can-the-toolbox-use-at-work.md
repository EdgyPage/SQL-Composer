# Which sqlglot APIs can the Toolbox use at work?

Type: research
Status: open
Blocked by: 02

## Question

Once the work environment's sqlglot version is known, establish which of the APIs the Toolbox
needs exist and behave identically on that version and on the version pinned on `dev`: the
builder functions, `exp.convert` and string-literal escaping for Hive, `qualify` and the errors it
raises, `lineage`, and the Hive generator's output for `INSERT OVERWRITE ... PARTITION`.

Recommend the version `dev` should pin so that tests there predict behaviour at work. Notes from
v1: `exp.Expr` is the base class only in recent versions, and minor releases are
backwards-incompatible by policy.

If the example database runs on sqlglot's executor (see "Can sqlglot's own executor run an
example database?"), the executor has its own version floor. `COUNT(DISTINCT)` silently returns
the row count on 30.18.0 and is fixed in 30.19.0; outer-join and NULL handling were fixed in
30.15.0. The current `dev` pin of 30.18.0 is therefore wrong for the example database even if it
is fine for generating SQL. Decide whether the pin moves, and what the example database does if
work has an older version.
