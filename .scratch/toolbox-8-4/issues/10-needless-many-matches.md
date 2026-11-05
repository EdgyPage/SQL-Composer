# Step 3 clears the needless many_matches

Type: task
Status: open
Blocked by: 01
Size: M

## Question

Step 1 adds `many_matches=True` and a `# CONVERSION:` mark to each join on a table whose Key
isn't answered yet, and nothing takes them out once step 3 writes the Keys (map, Q10, Q17).

## Done when

- `project.write_decisions`, once it writes a Key, builds each converted table of the batch
  again and takes out each `many_matches=True`, with its mark and its checklist note, whose
  Repeated-rows warning no longer fires. Its output names each one taken out.
- One still firing stays, as does every other opt-out and mark.
- A join on a table with no Key still warns and never stops.
- Only marks the Conversion wrote are taken out: a `many_matches=True` the user wrote, with no
  mark, stays.
- 01's journey answers the Key and sees the mark go.
