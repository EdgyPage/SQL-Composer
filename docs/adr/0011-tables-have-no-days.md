# A table's partitions are its own; nothing assumes days

Status: accepted, built by Toolbox 7.0; supersedes ADR 0007 where it adds a folder to each Saved
table's location, speaks of Partitions after the day, and drops old days, and ADR 0005 where a
Key holds for one day

Up to 6.1 the Toolbox treated a table as partitioned by one date column, its Date partition:
`Table(...)` had to be told one or `None`, every read bounded it at both ends, a Saved table was
written a day at a time, `run_tables(day)` ran a day, every Template was built around one, and a
Key named one row on one day. On 2026-10-21 the user called that assumption "distracting and
annoying and incorrect": different tables at work have different partitions, not every table
has a Key, and they create a table with a `SET` and a `CREATE ... LOCATION` path they work out
themselves, in a config file of their own.

So in 7.0:

- **A table's partitions are any columns, or none** (`partitioned_by=[...]`), and no column is a
  day to the Toolbox. `date_partition=` and `date_format=` are gone.
- **A read of a partitioned table must filter at least one of its partition columns**, unless it
  says `reads_all_partitions=True`. An unpartitioned table is never limited.
- **A write fills its partitions from the rows**, dynamically, or names some with
  `partition={...}`. Each notebook's `write()` chooses `INSERT_OVERWRITE` or `INSERT_INTO`.
- **A Key is optional.** Nothing is checked against a Key a table doesn't have; a join onto one
  still warns that it may repeat rows.
- **`location=` is the table's folder exactly as written.** The Toolbox adds no folder and needs
  no absolute path; it still refuses two Saved tables at one folder.
- **Day helpers stay as helpers**: `last_n_days`, `between`, `week_start` and `month_start` work on
  any date column, and mean nothing special to partitions.

## Considered options

- **Keep the Date partition as an optional special kind beside other partitions.** Rejected: two
  ways to say the same thing, and the user wanted the day gone, not optional.
- **Keep adding a folder of the table's own to `location=`**, as ADR 0007 chose. Rejected: the
  user builds each path themselves; the overlap check still stops two tables sharing one.
- **Generalize `by_day` into a split by partition.** Rejected: a loop over `partition={...}`
  writes does the same, with nothing new to learn.

## Consequences

- Every Table reference that names `date_partition=`, and every notebook that defines
  `write_day(day)`, changes: 7.0 is a major version, and its change notes say how. Passing
  `date_partition=` is refused, naming `partitioned_by=`.
- A read that bounded only its date now passes when it filters any partition column, so the read
  limit protects less of a table partitioned by several columns.
- Should a day-at-a-time workflow come back, it is written with `partition={...}` in the user's
  own loop, not in the Toolbox.
