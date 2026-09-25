# What does the example database demonstrate, and where does it run?

Type: prototype
Status: open
Blocked by: 08, 14

## Question

The user's idea (charting, Q2 elaboration): keep the hard composability guarantees by pairing
lightweight guard functions with an example database - a small set of made-up tables - that
*shows* each guarantee. For each guard, a careless Statement produces a visibly wrong number, and
the guarded one produces the right number or refuses with a clear message.

Build a rough version around one guarantee (duplicated rows under `SUM` is the obvious first) and
let the user react. Decide:

- which tables and rows - small enough to read by eye, big enough that each wrong number is
  obviously wrong;
- which demonstrations - one per guard that survives the guardrails ticket;
- how a demonstration is presented - a notebook, a script printing the two numbers side by side,
  a test, or all three;
- the engine it runs on, from the executor research;
- whether it ships to work alongside the Toolbox (as a learning aid) or stays on `dev` (as a test
  fixture), and whether it doubles as the fixture the test suite uses.

## Comments

**From "Which sqlglot APIs can the Toolbox use at work?" (2026-09-25).** The executor needs sqlglot
30.19.0 or newer. On an older version, the demonstrations stop with a plain message and can show
their pandas reference numbers instead, labelled as such.
