# Say only what is true of both Editions

Type: task
Status: open
Blocked by: 04, 13

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
  `tools/editions.py`).
- Regenerate `examples.html` and the golden.

## Done when

The Definition of done in `CLAUDE.md` holds, including the beginner reader over the changed
docstrings, refusal messages and Worked examples, with its report linked; the forbidden-word test
passes; the golden's Hive is byte-identical.
