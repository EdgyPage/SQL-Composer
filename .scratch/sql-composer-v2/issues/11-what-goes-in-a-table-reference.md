# What goes in a Table reference, and is it written or generated?

Type: grilling
Status: open
Blocked by: 01, 02

## Question

A Table reference is the Level 0 script for one table. It exposes the table's columns as
attributes, so a typo fails at import, together with the table's standard queries. Decide:

- what else it carries - column types, partition columns, a key, a one-line description;
- what a "standard query" is - for example the usual filters already applied, or the latest
  partition;
- whether the file is written by hand, or generated from a `DESCRIBE` run through the API and then
  edited. That depends on what the API returns.

## Comments

**From "Which guardrails on how a Statement is written earn their place?" (2026-09-25).** The Guards need three things from a Table reference:

- **a declared key.** `JOIN` onto a table with no key refuses unless it's given
  `many_matches=True`;
- **optional column types.** A typed column gets its values checked (`equals(runs.dt, 20260925)`
  against a string column refuses) and dates formatted to fit it. An untyped column falls back to
  the plain rules: a date becomes `'YYYY-MM-DD'`, and a timestamp with a time of day refuses;
- **a way to mark a column as not safe to add up,** for pre-summarised warehouse tables (distinct
  counts, averages, ratios).

**The user's idea (2026-09-25), raised during the guardrails grilling.** A function the user calls
once on an unknown table, which writes the Table reference file for them, above all its columns. The
user then adds the attributes that only they know by hand, such as "columns of interest" and "site
locations". The user doubts that those can be inferred from column names. Points to settle here:

- **What a metadata query can fill in:** column names, types, comments and partition columns
  (`DESCRIBE FORMATTED` or `SHOW CREATE TABLE`). It can't fill in the key (Hive doesn't enforce
  one), the columns that aren't safe to add up, or anything about meaning. Guessing a key by
  counting rows is a real query against a multi-million-row table, which load safety has to allow.
- **Regenerating mustn't overwrite the hand-written part.** Options: a generated file plus a
  hand-written file that imports it, or one file with a generated section that's rewritten in
  place.
- **Name:** the user proposed `RECORD(table)`. Upper-case names are reserved for clause functions,
  so this one wants a lower-case name.
- **It depends on what the query API returns** for a `DESCRIBE`, which the user knows from daily
  use. It reads metadata, not rows, which fits the "no probing at work" rule, but the user should
  confirm.
