# sqlglot Composer 7.1, exported 2026-10-22 13:22 - generated from dev, do not edit
"""What DESCRIBE and DESCRIBE FORMATTED say of a table: read once, and printed for stand-ins.

ask(...) sends DESCRIBE, or DESCRIBE FORMATTED, through your query and reads what comes back
into a Description, which answers in the Toolbox's words: the table's columns and their types,
its partition columns, its folder, whether it is managed, its file format, its Buckets and its
table properties. Warehouses print DESCRIBE in a few ways, and read(...) reads each of them, so
no other part of the Toolbox reads a label the warehouse prints.

The other way round, printed(...) gives what a warehouse prints for a Description, in each of
those ways, and of_table(...) the Description of the table a Table reference describes. A
StandIn, built from Table references, plays a warehouse holding their tables: it answers
DESCRIBE, DESCRIBE FORMATTED and SHOW PARTITIONS, and keeps each command it is sent. The
Example database's answers to DESCRIBE come from one, and so do the tests'.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pandas as pd

from .refusals import kind_name, need_warehouse_call, refuse
from .trees import SIMPLE_NAME
from .writing import hive_text

if TYPE_CHECKING:  # tables.py imports this file
    from .tables import Table

TOOLBOX_VERSION = "7.1"

# The three columns a warehouse prints DESCRIBE in, and the header Hive repeats them in.
DESCRIBE_COLUMNS = ["col_name", "data_type", "comment"]
COLUMNS_HEADER = ("# col_name", "data_type", "comment")
# The ways a warehouse prints DESCRIBE: Hive 3's own, with its details labelled with a colon and
# a table property on each line; a compact way, with no comment where there is none and the table
# properties on one line; and the compact way for a newer kind of table, which lists its
# partitioning as one row per column.
WAYS = ("hive3", "compact", "partitioning")

# DESCRIBE's headers, as Hive prints them: the partition list and its own column header, the
# partitioning a newer kind of table lists, and DESCRIBE FORMATTED's sections about the table
# itself. read knows each whatever its case.
PARTITION_INFORMATION = "# Partition Information"
COLUMN_HEADER = "# col_name"
PARTITIONING = "# Partitioning"
DETAILED_INFORMATION = "# Detailed Table Information"
STORAGE_INFORMATION = "# Storage Information"
DETAILS = (DETAILED_INFORMATION.lower(), STORAGE_INFORMATION.lower())
# The InputFormat each file format create_table writes is read with.
INPUT_FORMATS = {
    "ORC": "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat",
    "PARQUET": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
}


class Description:
    """What DESCRIBE, or DESCRIBE FORMATTED, says of one table, in the Toolbox's words.

    - `columns`: each column and its type, the table's own first, then its partition columns;
    - `descriptions`: the comment of each column that has one;
    - `partitioned_by`: its partition columns, in order.

    And from DESCRIBE FORMATTED alone, which DESCRIBE leaves as None, False or empty:

    - `location`: the table's folder, or None when none is listed;
    - `managed`: whether the warehouse keeps its files where it chooses;
    - `stored_as`: its file format, "ORC" or "PARQUET", or its InputFormat for any other, or
      None when none is listed;
    - `buckets`, `bucketed_by` and `sorted_by`: its Buckets, None and empty for none;
    - `properties`: its table properties.
    """

    def __init__(self, name: str, columns: dict[str, str], *,
                 descriptions: dict[str, str] | None = None,
                 partitioned_by: list[str] | None = None, location: str | None = None,
                 managed: bool = False, stored_as: str | None = None,
                 buckets: int | None = None, bucketed_by: list[str] | None = None,
                 sorted_by: list[str] | None = None,
                 properties: dict[str, str] | None = None) -> None:
        self.name = name
        self.columns = dict(columns)
        self.descriptions = dict(descriptions or {})
        self.partitioned_by = list(partitioned_by or [])
        self.location = location
        self.managed = managed
        self.stored_as = stored_as
        self.buckets = buckets
        self.bucketed_by = list(bucketed_by or [])
        self.sorted_by = list(sorted_by or [])
        self.properties = dict(properties or {})

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Description) and vars(self) == vars(other)

    def __repr__(self) -> str:
        return f"Description({', '.join(f'{k}={v!r}' for k, v in vars(self).items())})"


# --- Reading what the warehouse prints ----------------------------------------------------------


def ask(name: str, query: object, call: str, formatted: bool = False) -> Description:
    """Send DESCRIBE, or DESCRIBE FORMATTED, of the table `name` through `query`, for `call`,
    and read what comes back."""
    from .tables import table_node  # here, not at the top: tables.py imports this file

    command = "DESCRIBE FORMATTED" if formatted else "DESCRIBE"
    return read(name, _answer(query, f"{command} {hive_text(table_node(name))}", call))


def _answer(query: object, hive: str, call: str) -> pd.DataFrame:
    """Send `hive` through `query`, and refuse an answer that can't be read."""
    need_warehouse_call(call, "query", query, "It sends DESCRIBE to the warehouse, and reads "
                        "what the warehouse prints back.")
    frame = query(hive)
    if not isinstance(frame, pd.DataFrame):
        refuse(
            what=f"{call}: query gave back "
            f"{'None' if frame is None else kind_name(frame)} for {hive}.",
            why="It reads what the warehouse prints, as a pandas DataFrame.",
            fix="Make your query return the warehouse's answer as a DataFrame, as "
            "run_query(...) needs too.",
        )
    if len(frame.columns) == 0:
        refuse(
            what=f"{call}: query gave back a DataFrame with no columns for {hive}.",
            why="It reads what the warehouse prints, and there is nothing in it to read.",
            fix="Make your query return the warehouse's answer as it prints it.",
            error=ValueError,
        )
    return frame


def _cell(row: tuple[object, ...], at: int) -> str:
    """One cell of what the warehouse printed, as text, "" where it is empty."""
    value = row[at] if len(row) > at else None
    text = "" if value is None else str(value).strip()
    return "" if text in ("None", "nan") else text


def read(name: str, frame: pd.DataFrame) -> Description:
    """What DESCRIBE, or DESCRIBE FORMATTED, of the table `name` printed, as a Description,
    whichever way the warehouse prints it."""
    columns, descriptions, partitioned_by = {}, {}, []
    # DESCRIBE FORMATTED's lines about the table, by their labels in lower case without a
    # colon, and its table properties, which Hive lists a line each, and other warehouses on
    # one line, as [name=value, ...].
    details, properties = {}, {}
    # The columns come first; each header after them, bar the partition list's own column
    # header, starts a section, and only the partition sections name partition columns.
    section, label = "columns", ""
    for row in frame.itertuples(index=False):
        column, kind, comment = _cell(row, 0), _cell(row, 1), _cell(row, 2)
        if column.startswith("#"):
            if column.lower() != COLUMN_HEADER:
                section = column.lower()
            continue
        if section in DETAILS:
            if column:
                label = column.rstrip(":").strip().lower()
            _read_detail(details, properties, label, column, kind, comment)
            continue
        if column:
            _read_column(columns, descriptions, partitioned_by, section, column, kind, comment)
    buckets = _bucket_count(details.get("num buckets", ""))
    table_type = details.get("table type") or details.get("type") or ""
    return Description(
        name, columns, descriptions=descriptions, partitioned_by=partitioned_by,
        location=details.get("location"), managed="MANAGED" in table_type.upper(),
        stored_as=_stored_as(details.get("inputformat", "")), buckets=buckets,
        bucketed_by=_listed_names(details.get("bucket columns", "")) if buckets else [],
        sorted_by=_listed_names(details.get("sort columns", "")) if buckets else [],
        properties=properties)


def _read_column(columns: dict[str, str], descriptions: dict[str, str],
                 partitioned_by: list[str], section: str, column: str, kind: str,
                 comment: str) -> None:
    """Keep one line of DESCRIBE's columns, or of its partitions: a column, its type and its
    comment, or a newer kind of table's partitioning, such as Part 0 with dt."""
    # DESCRIBE FORMATTED in Hive lists a partition column only under its partitions.
    if column not in columns and section in ("columns", PARTITION_INFORMATION.lower()):
        columns[column] = kind
        if comment:
            descriptions[column] = comment
    if section == PARTITION_INFORMATION.lower():
        partitioned_by.append(column)
    elif section == PARTITIONING.lower() and SIMPLE_NAME.fullmatch(kind):
        partitioned_by.append(kind)


def _read_detail(details: dict[str, str], properties: dict[str, str], label: str, column: str,
                 kind: str, comment: str) -> None:
    """Keep one line of DESCRIBE FORMATTED's details: a labelled value, or, under Hive's
    "Table Parameters:", a table property on a line of its own."""
    if column:
        details[label] = kind
        if label == "table properties":  # all on one line: [name=value, name=value]
            pieces = []
            for piece in kind.strip().removeprefix("[").removesuffix("]").split(", "):
                if "=" in piece or not pieces:
                    pieces.append(piece)
                else:
                    pieces[-1] += ", " + piece
            properties.update(piece.split("=", 1) for piece in pieces if "=" in piece)
    elif label == "table parameters" and kind:
        properties[kind] = comment


def _bucket_count(text: str) -> int | None:
    """The number of Buckets DESCRIBE FORMATTED lists, or None for none: Hive lists -1."""
    try:
        number = int(text)
    except ValueError:
        return None
    return number if number > 0 else None


def _stored_as(input_format: str) -> str | None:
    """The file format DESCRIBE FORMATTED's InputFormat reads: ORC, PARQUET, the InputFormat
    itself for another, or None when it lists none."""
    if not input_format:
        return None
    for name in INPUT_FORMATS:
        if name.lower() in input_format.lower():
            return name
    return input_format


def _listed_names(text: str) -> list[str]:
    """The columns of DESCRIBE FORMATTED's Bucket Columns or Sort Columns: Hive's [a, b] or
    [Order(col:a, order:1)], or [`a`, `b`], in lower case, as the warehouse keeps them."""
    if "col:" in text:
        return [name.lower() for name in re.findall(r"col:\s*([^,)\s]+)", text)]
    inner = text.strip().removeprefix("[").removesuffix("]")
    return [name.strip().strip("`").lower() for name in inner.split(",") if name.strip()]


# --- Printing a table as the warehouse would --------------------------------------------------


def of_table(t: Table, *, location: str | None = None, managed: bool = False,
             stored_as: str | None = None, lacking: tuple[str, ...] = ()) -> Description:
    """The Description of the table a Table reference describes, as create_table makes it, but
    for what the warehouse's table has otherwise: another `location`, `managed`, another file
    format, `stored_as`, or none of the columns `lacking`. Each column's comment is its
    `descriptions=` entry, which create_table never writes: a stand-in shows them, as the
    Example database's DESCRIBE does."""
    from .tables import property_pairs  # here, not at the top: tables.py imports this file

    partitions = [column for column in t._partitioned_by if column not in lacking]
    own = [column for column in t._columns if column not in t._partitioned_by + list(lacking)]
    columns = {column: t._columns[column] or "" for column in own + partitions}
    return Description(
        t._name, columns,
        descriptions={column: text for column, text in t._descriptions.items()
                      if column in columns},
        partitioned_by=partitions, location=location or t._location, managed=managed,
        stored_as=stored_as or t._stored_as, buckets=t._buckets,
        bucketed_by=[column.lower() for column in t._bucketed_by],
        sorted_by=[column.lower() for column in t._sorted_by], properties=dict(property_pairs(t)))


def printed(described: Description, formatted: bool = False,
            way: str = "hive3") -> pd.DataFrame:
    """What DESCRIBE, or DESCRIBE FORMATTED, prints for a Description, printed the way
    `way` names, one of WAYS."""
    if way not in WAYS:
        raise ValueError(f"printed(..., way={way!r}): use one of {', '.join(WAYS)}.")
    if way == "hive3":
        rows = _hive_columns(described, formatted)
        if formatted:
            rows += _hive_details(described)
    else:
        rows = _compact_columns(described, way)
        if formatted:
            rows += _compact_details(described)
    return pd.DataFrame(rows, columns=DESCRIBE_COLUMNS)


def _hive_columns(described: Description,
                  formatted: bool) -> list[tuple[str, str | None, str | None]]:
    """Hive's columns: all of them, then the partition columns again under their header; or,
    formatted, the table's own columns under a header, then the partition columns only under
    theirs, each part followed by a blank row."""
    partitions = described.partitioned_by
    listed = [("", None, None), (PARTITION_INFORMATION, None, None), COLUMNS_HEADER,
              *[_hive_column(described, column) for column in partitions]]
    if not formatted:
        return ([_hive_column(described, column) for column in described.columns]
                + (listed if partitions else []))
    own = [column for column in described.columns if column not in partitions]
    return ([COLUMNS_HEADER, *[_hive_column(described, column) for column in own]]
            + (listed if partitions else []) + [("", None, None)])


def _hive_column(described: Description, column: str) -> tuple[str, str | None, str | None]:
    return (column, described.columns[column], described.descriptions.get(column, ""))


def _hive_details(described: Description) -> list[tuple[str, str | None, str | None]]:
    """DESCRIBE FORMATTED's details, as Hive prints them."""
    rows = [(DETAILED_INFORMATION, None, None),
            ("Database:", described.name.rpartition(".")[0], None)]
    if described.location is not None:
        rows.append(("Location:", described.location, None))
    rows.append(("Table Type:", "MANAGED_TABLE" if described.managed else "EXTERNAL_TABLE",
                 None))
    if described.properties:
        rows += [("Table Parameters:", None, None),
                 *[("", name, value) for name, value in described.properties.items()]]
    rows += [("", None, None), (STORAGE_INFORMATION, None, None)]
    if described.stored_as is not None:
        rows.append(("InputFormat:", _input_format(described.stored_as), None))
    sorted_by = ", ".join(f"Order(col:{column}, order:1)" for column in described.sorted_by)
    rows += [("Num Buckets:", str(described.buckets or -1), None),
             ("Bucket Columns:", f"[{', '.join(described.bucketed_by)}]", None),
             ("Sort Columns:", f"[{sorted_by}]", None)]
    return rows


def _compact_columns(described: Description,
                     way: str) -> list[tuple[str, str | None, str | None]]:
    """The compact way's columns: all of them, with no comment where there is none, then the
    partition columns again, or a newer kind of table's partitioning."""
    rows = [(column, kind, described.descriptions.get(column))
            for column, kind in described.columns.items()]
    partitions = described.partitioned_by
    if partitions and way == "partitioning":
        rows += [("", "", ""), (PARTITIONING, "", ""),
                 *[(f"Part {number}", column, "") for number, column in enumerate(partitions)]]
    elif partitions:
        rows += [(PARTITION_INFORMATION, "", ""), COLUMNS_HEADER,
                 *[(column, described.columns[column], described.descriptions.get(column))
                   for column in partitions]]
    return rows


def _compact_details(described: Description) -> list[tuple[str, str | None, str | None]]:
    """DESCRIBE FORMATTED's details, the compact way: labels with no colon, and the table
    properties on one line."""
    database, _, table = described.name.rpartition(".")
    rows = [("", "", ""), (DETAILED_INFORMATION, "", ""), ("Database", database, ""),
            ("Table", table, ""), ("Type", "MANAGED" if described.managed else "EXTERNAL", "")]
    if described.location is not None:
        rows.append(("Location", described.location, ""))
    if described.stored_as is not None:
        rows.append(("InputFormat", _input_format(described.stored_as), ""))
    if described.buckets:
        rows += [("Num Buckets", str(described.buckets), ""),
                 ("Bucket Columns", _quoted_names(described.bucketed_by), ""),
                 ("Sort Columns", _quoted_names(described.sorted_by), "")]
    if described.properties:
        listed = ", ".join(f"{name}={value}" for name, value in described.properties.items())
        rows.append(("Table Properties", f"[{listed}]", ""))
    return rows


def _quoted_names(names: list[str]) -> str:
    return "[" + ", ".join(f"`{name}`" for name in names) + "]"


def _input_format(stored_as: str) -> str:
    """The InputFormat a file format is read with: ORC's or Parquet's, or `stored_as` itself,
    already one, for any other."""
    return INPUT_FORMATS.get(stored_as, stored_as)


# --- A stand-in warehouse ---------------------------------------------------------------------


class StandIn:
    """A stand-in for your query and execute: a warehouse holding the tables of some Table
    references, or of Descriptions, which never runs a query.

    Called as query, it answers DESCRIBE and DESCRIBE FORMATTED of each table, printed the
    way `way` names, one of WAYS, and SHOW PARTITIONS with the Partitions `partitions` gives
    it, such as {"ops.runs": ["dt=2026-09-24"]}; any other query gives back a copy of `rows`,
    by default a DataFrame with nothing in it. Each command it is sent, through query or
    execute, is kept in `sent`. It refuses a table it doesn't hold, as a warehouse does.
    """

    def __init__(self, *tables: Table | Description, way: str = "hive3",
                 partitions: dict[str, list[str]] | None = None,
                 rows: pd.DataFrame | None = None) -> None:
        self.tables = {_key(t.name if isinstance(t, Description) else t._name):
                       t if isinstance(t, Description) else of_table(t) for t in tables}
        self.way = way
        self.partitions = {_key(name): list(listed) for name, listed in
                           (partitions or {}).items()}
        self.rows = pd.DataFrame() if rows is None else rows
        self.sent: list[str] = []

    def __call__(self, hive: str) -> pd.DataFrame:
        """Answer `hive` as query does, and keep it."""
        self.sent.append(hive)
        return self.answer(hive)

    def execute(self, hive: str) -> None:
        """Keep `hive`, as execute sends it, and change nothing."""
        self.sent.append(hive)

    def answer(self, hive: str) -> pd.DataFrame:
        """What a warehouse holding these tables gives back for `hive`, kept nowhere."""
        words = hive.split()
        command = [word.upper() for word in words[:2]]
        if command[:1] == ["DESCRIBE"]:
            described = self._held(words[-1])
            return printed(described, command == ["DESCRIBE", "FORMATTED"], self.way)
        if command == ["SHOW", "PARTITIONS"]:
            described = self._held(words[-1])
            if not described.partitioned_by:
                raise ValueError(f"Table {described.name} is not a partitioned table.")
            return pd.DataFrame({"partition": self.partitions.get(_key(described.name), [])})
        return self.rows.copy()

    def _held(self, name: str) -> Description:
        """The table it holds by this name, whatever its case or backticks."""
        if _key(name) not in self.tables:
            raise RuntimeError(f"Table not found: {name}")
        return self.tables[_key(name)]


def _key(name: str) -> str:
    """A table's name as a warehouse reads it: in any case, a name in backticks or not."""
    return ".".join(part.strip("`") for part in name.strip().split(".")).lower()
