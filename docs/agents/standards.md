# Standards

What the code reviewer judges on `dev`. It holds only what no test can check: anything a test
can hold lives in `pytest`, and isn't repeated here. The `code-review` skill reads this file as
the repo's coding standards.

## Beginner readability

The Toolbox's user is Python-first and new to SQL. Read every change as they would, on first
contact: a Statement, a docstring, a refusal message. A change passes when they could follow it
without stopping to study it. Some safety complication may stay, if it reads plainly.

## Glossary words

Code, docstrings and refusal messages use the words in `CONTEXT.md`, and none of the words it
says to avoid. A new domain word is added to the glossary in the same change, or not used.

## No abstraction to study first

No class hierarchy, decorator, metaclass, registry or other machinery the user has to learn
before they can use a function. A plain function with plain arguments wins over a cleverer
shape, even at the cost of some repetition.

## No new public name without a ticket

The Toolbox's public names are decided in the tracker. A change that adds, removes or renames
one points at the ticket that decided it.

## Parity

Both Editions show a user the same thing: the same names, messages, docstrings and Worked
examples, and the same Hive. Everything they share is written once, in `composer_core/`, so
parity is about each Edition's own files. A change to one Edition's writing or engine file, such
as `sqlglot_composer/writing.py`, is made in the other's too, unless the Hive has to differ;
then the difference is a row of `DECLARED_DIFFERENCES` in `tools/editions.py`, with its reason,
and nowhere else. Only what concerns an Edition's own library may differ otherwise: the checks
and messages that name sqlglot or pyspark, and how its Example database runs.

## Nothing reaches the network

A new entry in `ALLOWED`, in `tools/offline_policy.py`, gives its reason and has the user's OK,
asked for in the session or the ticket (ADR 0004). A change that adds an entry without both
fails review, however local the site looks.
