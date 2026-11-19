# The two paths tied, rule by rule

Type: task
Status: open
Blocked by: 05, 06, 11
Size: M

## Question

How the code and the Copilot files are kept saying the same thing, neither the other's
reference (round 2, Q5; ADR 0016: "Both paths, equal").

## Done when

- **Every rule ID** in files 11, 12, 15 and 20 has a test of the code giving the Hive the rule
  gives, and every such test names its rule ID.
- **A repo test** fails when a Copilot file holds a rule ID with no test, or a test names an ID
  no Copilot file holds.
- `docs/agents/standards.md` says a rule changes in both places in one commit.
