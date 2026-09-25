# What's in the Toolbox?

Type: grilling
Status: open
Blocked by: 01, 08, 09, 10

## Question

With the syntax, the guardrails, the load behaviour and the way pieces combine all settled, fix
the function list:

- the clause functions - the user's "SELfunc(params) FROMfunc(params)";
- calculations - date bucketing, safe division, conditional counts;
- common patterns - latest row per key, top N per group;
- the output side - to a Hive string, to a lineage HTML file.

Every function ships with a worked example in its docstring. Keep the count small enough to read
in one sitting, and note anything the user could just as well write in plain Python.
