# Which guardrails on how a Statement is written earn their place?

Type: grilling
Status: resolved
Blocked by: 01, 03

## Question

A Python-first SQL beginner gains most from guards against the mistakes they are likely to make,
but every guard is also one more thing to understand. The user's steer (charting, Q2
elaboration): v1's *guarantees* can come back, as long as each is a lightweight function rather
than a model to learn, and each is shown working on the example database. Given the chosen
syntax, decide which guards stay and how each announces itself:

- typo-proof columns through Table references (settled in spirit during charting);
- escaped literals;
- a Hive-validity check before a string is handed over;
- **duplicated rows**: a join on a non-key column multiplies rows and silently inflates a `SUM`.
  Catching it needs a Table reference to declare its key;
- **unsafe re-grouping**: moving from days to weeks is safe for a `SUM` but wrong for a
  `COUNT(DISTINCT ...)` or an average of averages, and a ratio must be recomputed from its parts;
- anything the Hive research surfaces.

For each guard: refuse or warn, how to opt out, what the message says, and the smallest function
that expresses it - no Metric/Dimension vocabulary. This ticket is about the *shape* of a
Statement; how much it reads and returns belongs to the load-safety ticket.

## Comments

**From "How does a composed Statement read?"** The syntax is clause functions, with conditions as
named functions (`equals(col, value)`). The prototype's probe of value conversion found four traps
this ticket should rule on, since every literal goes through `sqlglot.exp.convert`:

- `equals(col, None)` emits `col = NULL`, which matches nothing. Refuse it, or emit `IS NULL`?
- `float("nan")`, common in values taken from a DataFrame, silently becomes `NULL`.
- A numpy `True` (`np.bool_`) crashes with `Cannot convert True`. numpy int and float convert fine.
- `pd.Timestamp` / `datetime.date` become `CAST('...' AS TIMESTAMP/DATE)`. Compared against a
  string partition column like `dt`, this may defeat partition pruning.

The Statement ticket already settled one guard: `SELECT` refuses an unnamed calculation, which
would otherwise reach pandas as `_c1`. Strings are escaped by construction (`O'Brien` becomes
`'O\'Brien'`).

**From "Which sqlglot APIs can the Toolbox use at work?" (2026-09-25).** Two more candidates:
`exp.convert(float("inf"))` emits a bare `inf`, and hand-built arithmetic nodes get no brackets
(`SUM(a) / b + 1` for what should be `SUM(a) / (b + 1)`).

## Answer

**Every Guard refuses; none warns.** A Guard stops the Statement at the earliest call that has
everything it needs (`JOIN(...)`, `SUM(...)` or `statement(...)`), so the traceback points at the
user's line. The only way past is an opt-out keyword on that same call, named for what the user
accepts. There is no global switch.

Every refusal raises one Toolbox exception type (`GuardRefused`) and says four things:

1. what happened, naming the columns and tables;
2. why the number comes out wrong, in one plain sentence with no SQL jargon;
3. the usual fix;
4. the opt-out, as code to paste.

Load limits (how much a Statement reads and returns) are a separate thing, not Guards: they
protect the cluster, not the answer.

The Guards that stay:

| Guard | Refuses | Fix / opt-out |
| --- | --- | --- |
| Typo-proof columns | an attribute that isn't a column of its Table reference or Derived table | none; fails at import with the column list |
| Unnamed calculation | a calculation in `SELECT` without `AS(...)` (settled by "How does a composed Statement read?") | none |
| `None` in a condition | `None` in `equals`, `not_equals` or `any_of` | use `is_null(col)` / `is_not_null(col)` |
| NaN and `inf` | either value anywhere in a condition, naming its position | drop them first; no opt-out |
| Timestamp with a time of day | a `Timestamp`/`datetime` that isn't midnight, until column types exist | none yet (see "What goes in a Table reference, and is it written or generated?") |
| Repeated rows | `JOIN(T, ON=...)` where `ON` doesn't pin down T's whole key, or T declares no key | group T first; `many_matches=True` |
| Unsafe re-grouping | `SUM` or `AVG` over a column made by a distinct count, an average or a division, or one a Table reference marks the same way | keep the parts and recompute; `adds_up=True` |
| Missing `GROUP_BY` column | a plain selected column left out of `GROUP_BY` when the Statement aggregates | none; Hive would refuse anyway |
| `LEFT JOIN` then `WHERE` on its table | a `WHERE` condition on the right-hand table of a `LEFT_JOIN` | move it into `ON`; `keeps_only_matches=True` |
| Cross join | `JOIN` without `ON` | use `CROSS_JOIN(t)`, whose name is the opt-out |

What isn't a Guard:

- **Escaping holds by construction.** There is no raw-SQL entry point. A Hive function the Toolbox
  doesn't wrap goes through a generic call such as `hive_function("regexp_extract", col, pattern,
  1)`, which still escapes its arguments.
- **Quiet fixes, because nothing comes out wrong:**
  - numpy scalars become plain Python (`.item()`);
  - a `date`, or a midnight `Timestamp`/`datetime`, becomes the string `'2026-09-25'`, never a
    `CAST`, so a string partition column still prunes;
  - arithmetic is always built bracketed.
- **A self-check in `to_hive`:** the string is parsed back with sqlglot's Hive dialect and must come
  out the same. If it doesn't, the message says it is a Toolbox bug, not the user's.
- **`not_equals` and `any_of` dropping NULL rows** (pandas `!=` keeps them) is documented in their
  docstrings and shown in the example database. It isn't guarded, because that would need every
  column's nullability.

Handed on:

- **"What goes in a Table reference, and is it written or generated?"** A Table reference needs
  a declared key, optional column types (a typed column gets its values checked and dates
  formatted to fit), and a way to mark a column as not safe to add up.
- **"How much may a Statement touch and return by default?"** It takes five of the Hive
  research's six defaults: bounded partition filter, automatic `LIMIT`, no `ORDER BY` without
  `LIMIT`, no `OFFSET`, no `*`. Cross joins stay here.
- **"What's in the Toolbox?"** It gets `is_null`, `is_not_null`, `LEFT_JOIN`, `CROSS_JOIN` and
  `hive_function`.
- **"What does the example database demonstrate, and where does it run?"** One demonstration per
  Guard that can give a wrong number: repeated rows, re-grouping, `LEFT JOIN` + `WHERE`, `None`
  and NaN. Plus `not_equals` dropping NULLs.
