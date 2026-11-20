# A Formula workbook converts in code, beside the Copilot files

Status: accepted 2026-11-19, to be built by Toolbox 8.9; reverses the 7.2 map's "a Copilot file,
no Toolbox code" for Excel, and extends ADR 0014's Conversion to a second kind of input

7.2 turned Excel workbooks into Hive with Copilot files alone, as the user then put it: "While
the excel conversion is useful, it's not going to happen often enough to make code for it."
By 8.8 those files, 11, 12 and 15, hold about 25,000 characters loaded together, and still
leave every PivotTable alone, though the people the Excel path is for build their work on
pivots. The user: "The excel conversion text instructions have bloated to the point I wanted to
avoid by not making code conversions an explicit feature, but I think it's time to make the
code."

So the convert Workflow reads a Formula workbook in its batch, beside scripts of Hive, and the
Copilot files stay:

- **Any mix converts.** A workbook's calculations may sit in a Table's formulas, Power Query
  steps and PivotTables, reading each other in any order: what reads what decides each piece's
  part, as it does in the Copilot files. The user: "the dependency graph fixes all of it so the
  format of the intermediate transforms doesn't matter for users." Data still sits in Tables:
  file 11's refusal of a formula outside a Table holds on both paths.
- **Two paths, equal.** The user: "My non-technical users will likely use copilot, I'll use the
  code." Neither path is the other's reference: each is tested on its own, on the same tasks and
  by the same Workbook check, and each rule of the Copilot files is tied to a test of the code
  giving the same Hive, so the two can't drift apart unnoticed.
- **A pivot converts as what it shows.** Its Row and Column fields are the GROUP BY, a Column
  field as rows, so a new value flows in; its values the aggregates, Show Values As a Window;
  the totals it shows each a final of its own, since a Saved table holds no Subtotal row; a
  calculated item a column beside the real rows, "regardless of whether or not it's strictly
  normalized", so every aggregate the pivot showed can be read from the table.
- **A Pivot filter is written in, and its scaling is a Decision.** Each filter the workbook was
  saved with is the condition it is. Its Decision keeps it by default, or keeps every slice:
  folded into the grain, one batch per value as a Run value, or a table per value, each layer
  with the count of tables it would make. The user: "a filter with 100 conditions would make
  100 tables, but the higher layer filter may have only 3, which is manageable."
- **The Workbook check never reads the warehouse.** Each final's rows are worked out from the
  workbook's own Tables on this computer and compared with the values Excel stored. The user:
  "the actual sql will likely conflict with the old data inside an excel file."

## Considered options

- **Keep Copilot files alone, as 7.2 chose.** Rejected: the files have grown past what the user
  wanted to maintain, and pivots would need more.
- **Code alone, the Copilot files retired.** Recommended at first, to free two files. Rejected
  by the user: the people the Excel path is for will use Copilot.
- **The code as the reference the Copilot files follow.** Recommended at first. Rejected by the
  user for two equal paths, each tested for itself.
- **A Column field written wide, a column per value**, as the pivot looks. Rejected: a value the
  sample didn't hold would never appear; Copilot offers the wide shape as an add-on.
- **Refuse calculated items**, as they change a field's rows. Rejected by the user: a column
  keeps what the person expects from their table.
- **Check against the warehouse through `query`.** Rejected: the warehouse's rows have moved on
  from the workbook's, so every difference would be noise.

## Consequences

- One workbook reader, standard library only, in the Toolbox's folder, reads pivots too;
  `copilot/workbook_text.py` loads it by its path, so it still needs nothing but Python.
- The Workbook check runs Hive with sqlglot's executor: two more Toolbox files import sqlglot,
  the check's own and the executor's, moved whole from dev's Example database so that windows
  and grouping sets run in one place (ticket 09), and the registry says so.
- Copilot files 20 (PivotTables into Hive, and the `-- Pivot filter:` mark convert reads into
  the same Decision) and 21 (growing a converted pivot) join 11, 12 and 15.
- About 40 pivot tasks join the Excel evaluation; its workbooks are written by a dev tool, a
  query on a Power Query sheet, so the offline policy's refusal of a workbook's Power Query is
  unchanged.
- 8.9's Upgrade step has nothing to change in a Project.
