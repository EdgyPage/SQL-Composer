# Formulas and roles into Hive, in code

Type: task
Status: open
Blocked by: 01
Size: XL

## Question

The code path's first half: each piece's role (file 15's P1 to P11, R1 to R3) and each formula's
Hive (file 11's rules), written by the Toolbox (ADR 0016).

## Done when

- **Roles** from the reader's Order: source, step, final, summary final, settings
  (Parameters, Keys), left out, refused in a loop; a query and the Table it loads are two
  pieces.
- **Each final's Hive** as sqlglot trees: sources as `<database>.<table>`, steps as CTEs in
  order, columns in the Table's order, a Parameters value written in, a typed-over value a
  CASE on its Keys row (V1, V2), a summary's groups written in (R1).
- **Each rule of file 11 by its ID**, F1 to F10, I1 to I6, V1, V2, M1 to M5, X1: converted,
  converted with its mark, or refused as `NULL AS` its header and named. A header that isn't a
  plain name is written as file 11's N2 says.
- What it gives back: each final's Hive, and a list of what was written in, marked, refused and
  left alone, in file 15's map's words.
- **No new public name yet**: ticket 07 gives the user's call.
- Tests: one per rule ID, its formula giving the Hive the rule gives; file 15's and file 11's
  Worked patterns each as a test.
