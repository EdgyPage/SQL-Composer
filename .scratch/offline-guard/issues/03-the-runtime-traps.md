# The runtime traps

Type: task
Status: open
Blocked by: 01
Size: S

## Question

Plan steps 4 and 5: `tests/offline_trap.py`, an audit hook installed by tests/conftest.py in both Editions' runs, and `_refuse_the_network()` in spark_composer/engine.py's child before pyspark loads.

## Done when

- Both runs pass with the trap on; a non-loopback lookup is refused in the test Python and in the Spark child.
- Both runs pass, the code-review skill has run with this ticket as its spec, and its drift
  items are closed (CLAUDE.md's Definition of done).
