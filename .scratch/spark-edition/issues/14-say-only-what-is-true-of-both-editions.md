# Say only what is true of both Editions

Type: task
Status: resolved
Blocked by: 04, 13

Findings: [ticket 04](../findings/04-spark-reads-the-hive.md) gives the evidence and wording
this ticket uses.

## Question

The shared files will ship in both folders, so every sentence in them must be true of both. The
user agreed that claims holding only on Hive, or naming sqlglot, are reworded; the Edition facts
move to the README and the CHANGES 3.0 draft.

- Reword every claim ticket 4's claims table found untrue on Spark, with its proposed wording.
- Reword the sentences that name sqlglot: `sql_composer/calculations.py:276-277`, `:334-336` and
  `:358-359`; `sql_composer/running.py:239-241`; `sql_composer/example_database.py:1-7`.
- Give `sql_composer/__init__.py` a first line without the product name (it becomes the
  cheat-sheet line) and reword `:9-10`.
- In the Worked examples, `regrouping.py:5-6` and `latest_and_top_n.py:6-7` say "where the
  Example database can't run it".
- Turn on the repo test that the canonical shared files hold no forbidden word (the list lives in
  `tools/editions.py`): remove the strict xfail from
  `tests/repo/test_editions.py::test_no_canonical_shared_file_names_what_only_one_edition_has`.
- Word `sql_composer/CHANGES.md` without either folder's or product's name: it is a verbatim file,
  copied byte for byte into Spark Composer's folder (ticket 06).
- Regenerate `examples.html` and the golden.

## Done when

The Definition of done in `CLAUDE.md` holds, including the beginner reader over the changed
docstrings, refusal messages and Worked examples, with its report linked; the forbidden-word test
passes; the golden's Hive is byte-identical.

## Answer

Every claim ticket 04's claims table found untrue on Spark now holds on both engines (`10f2db8`,
then the review fixes). A calculation's made-up name, NaN and infinity, the order of rows in a
Derived table, a sort without LIMIT, division by zero, a table that already exists, the Tez caveat,
the week function and a type mismatch each say what holds on Hive and on Spark. The claims that
held on both mostly stay as they were. A few now say "the warehouse" for the same reason, such as
reading every day of a table.

**The warehouse** is a new glossary word in CONTEXT.md: where Statements run at work, the tables
and the Hive or Spark that runs a Statement's Hive on them. The refusals and docstrings use it
wherever the engine is either one.

No shared file names sqlglot any more. The forbidden-word test holds every canonical shared file,
with no expected failure left. `__init__`'s first line has no product name. The Worked examples
say their results are computed in pandas, so they show even where the Example database can't run
`week_start` or `row_number`. CHANGES.md names neither folder, since both folders ship it as it is.
The golden's Hive is byte-identical; two refusals it pins read differently.

## Comments

**Code review (2026-09-29), `10f2db8`.**

- *Standards:*
  - **Fixed:**
    - "The warehouse" is a glossary word.
    - "Every warehouse" is gone: GROUP_BY keeps its old reason, and week_start says Hive and
      Spark have no week function that works the same on both.
    - hive_function's sentence is shorter and no longer makes "the Hive" act.
    - AS says / divides as Python's does.
    - The NaN refusal no longer says "the comparison", which was false for arithmetic (D29).
    - `__init__` says "if this Python can't run the Toolbox".
    - `saved_table.py`'s create step says the warehouse refuses.
    - `_string_literal`'s docstring fits the line length.
  - **Answered, not changed:** each claim lives in several places, a refusal and the docstrings
    around it. The standards prefer repetition to machinery, and this change rewords every
    copy.
- *Spec:*
  - **Fixed:**
    - The made-up name says "such as _c0 or count(1)".
    - A type mismatch "could quietly match nothing or the wrong rows, or stop with an error".
    - A Derived table's order "may not" be kept (Hive never keeps it).
    - `derived` says the warehouse "usually" works the table out again.
    - `check_table_reference` says "a table the warehouse can't describe".
  - **Answered, not changed:** "dividing by zero gives NULL" holds on Spark once ticket 17's
    printer writes NULLIF, and week_start's "a day like 2026-09-21" once ticket 25's CAST lands,
    as planned.

**Beginner reader (2026-09-29):**
[reports/14-beginner-reader.md](../reports/14-beginner-reader.md). Its three costliest stops were
answered:

- A sort without LIMIT now says why pandas is better: the warehouse puts every row in order
  before any comes back, and pandas sorts the rows once you have them.
- The Worked examples no longer read as if the Example database could run week_start only
  sometimes. The results are computed in pandas, "so they show even where" it can't.
- "The warehouse" is defined, used for one thing, and never plural. The control-character
  refusal says "the Toolbox would write it", not "the Hive".

The smaller stops were answered too: the NaN reason, the derived-order opt-out's "it", the
`__init__` "it"s, GROUP_BY's "which", Tez ("ask whoever looks after it"), to_hive's "written by
whom", and DESCRIBE, now introduced where Table first names it. The CHANGES line on control
characters says "Hive and Spark".
