# A Conversion keeps what converts and leaves the rest Unchecked at the smallest size

Status: accepted 2026-10-26, to be built by Toolbox 7.2; extends ADR 0006's Unchecked statement

The user has other people's Hive to bring under their own patterns: SELECTs hundreds of lines
long, with CTEs, many joins, long hand-written IN lists and CASE chains, "built on the
unscalable assumption of ad-hoc rigor". 7.2 adds the Conversion, a Project action that reads such
Hive and writes the user's Composer code for it.

Some of that Hive the Clause functions can't write yet. ADR 0006's escape hatch, the Unchecked
statement, is a whole statement: one `LATERAL VIEW explode` would leave all 400 lines opaque.
The user asked for the fallback to be Unchecked, and for the 80% that converts: "I'd rather have
80% of what I need to prevent converting it all statements by hand."

So the fallback goes only as wide as it must:

- **A Hive function the Toolbox doesn't wrap** converts to `hive_function(...)`, which is checked.
- **An expression that can't be written**, such as a construct with no Clause function, becomes
  an **Unchecked expression**: its Hive kept as text, standing in for one Column
  (`unchecked_column`) or one Condition (`unchecked_condition`) inside an otherwise converted
  Clause function. The Toolbox reads which columns the text names, so Lineage traces it and the
  Guards check the rest of the Statement.
- **A CTE that can't be written as a Statement**, such as one built on `LATERAL VIEW`, becomes
  an **Unchecked derived table** (`unchecked_derived`): named, with its output columns, read by
  the rest as any Derived table is, and one opaque box in Lineage.
- **Only a top-level query the Toolbox can't read at all** becomes an Unchecked statement.
- **A join or read that a Guard would refuse** is converted with its opt-out, marked
  `# CONVERSION:`, so the converted Statement gives the original's rows and each risk is left for
  the user to decide.

Each Unchecked piece is a call whose name starts `unchecked_`, so a search finds every one, and
the Conversion's scan counts them. As with ADR 0006, each marks something the Toolbox should
learn to write.

## Considered options

- **Refuse the whole Conversion and list what's missing.** Recommended at first, to keep
  "silently wrong" out. Rejected by the user: a list of 20 gaps leaves all 400 lines to write by
  hand.
- **Fall back to one Unchecked statement for the whole query.** What the user first chose;
  rejected together once it was clear it gives 0% whenever anything fails.
- **Convert the rest and leave a placeholder that won't run** where a piece fails. Rejected:
  the converted notebook wouldn't run until every gap was filled, so it couldn't be compared
  with the original.
- **Leave the Guards' opt-outs out**, so each refuses until the user decides. Rejected: the
  converted notebook wouldn't run, and the rows couldn't be compared.

## Consequences

- Three public names join `unchecked_hive`, each a Worked example and in the gallery.
- An Unchecked expression or derived table sits inside a Statement the Guards otherwise check,
  so the Guards and Load limits must say plainly when one can't look inside it.
- `project.check()` lists every `# CONVERSION:` mark left in the Project, as it lists an
  Upgrade's `# UPGRADE` marks.
- The Conversion's checks compare the converted Statement with the original twice: by its Hive,
  normalised by sqlglot, always; and by its rows, through the user's `query`, when they ask.
