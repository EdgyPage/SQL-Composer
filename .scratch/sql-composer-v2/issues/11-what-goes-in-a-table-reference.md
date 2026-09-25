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
