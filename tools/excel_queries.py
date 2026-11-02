"""Save Power Queries into a workbook the way Excel saves them, for dev's tests and evaluations.

openpyxl writes no Power Query, so a workbook built with it holds none. This adds them to the
saved file, as Excel does ([MS-QDEFF]):
- a `customXml` item, the DataMashup: base64 of a version, then a zip whose
  Formulas/Section1.m holds every query's M, then the package's permissions and metadata;
- a connection for each query in `xl/connections.xml`, naming the query;
- for each query that loads a Table, a query table beside the Table, which names that
  connection.

`copilot/workbook_text.py` reads them back, as it reads a workbook Excel saved. Whether Excel
itself opens the result as it opens its own is untested: dev has no Excel.
"""

from __future__ import annotations

import base64
import io
import re
import struct
import zipfile
from xml.sax.saxutils import escape, quoteattr

SPREADSHEET = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELATIONSHIP_TYPES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_RELATIONSHIPS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
MASHUP = "http://schemas.microsoft.com/DataMashup"
CUSTOM_XML = "http://schemas.openxmlformats.org/officeDocument/2006/customXml"
TYPES = {
    "connections": "application/vnd.openxmlformats-officedocument.spreadsheetml."
                   "connections+xml",
    "queryTable": "application/vnd.openxmlformats-officedocument.spreadsheetml."
                  "queryTable+xml",
    "customXmlProps": "application/vnd.openxmlformats-officedocument."
                      "customXmlProperties+xml",
}
HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def _name(name: str) -> str:
    """A query's name as M shares it: plain, or #"..." when it isn't a plain name."""
    return name if re.fullmatch(r"[A-Za-z_]\w*", name) else '#"' + name.replace('"', '""') + '"'


def section(queries: list[tuple[str, str]]) -> str:
    """The section document every query's M is saved in, Formulas/Section1.m."""
    shared = "".join(f"\r\n\r\nshared {_name(name)} = {m.strip()};" for name, m in queries)
    return "section Section1;" + shared


def _package(queries: list[tuple[str, str]]) -> bytes:
    """The zip of the mashup's parts: its content types, its configuration, and its M."""
    items = "".join(
        "<Item><ItemLocation><ItemType>Formula</ItemType>"
        f"<ItemPath>Section1/{escape(name)}</ItemPath></ItemLocation><StableEntries />"
        "</Item>" for name, _ in queries)
    files = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="utf-8"?><Types xmlns="'
            f'{CONTENT_TYPES}"><Default Extension="xml" ContentType="text/xml" />'
            '<Default Extension="m" ContentType="application/x-ms-m" /></Types>'),
        "Config/Package.xml": (
            '<?xml version="1.0" encoding="utf-8"?><Package><Version>2.140.0.0</Version>'
            "<MinVersion>2.21.0.0</MinVersion><Culture>en-US</Culture>"
            "<SafeCombine>true</SafeCombine><Items>" + items + "</Items></Package>"),
        "Formulas/Section1.m": section(queries),
    }
    held = io.BytesIO()
    with zipfile.ZipFile(held, "w", zipfile.ZIP_DEFLATED) as package:
        for name, text in files.items():
            # A fixed time and system, so a package built twice, on any computer, holds the
            # same bytes: ZipInfo records the system it was made on.
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 0
            package.writestr(entry, text.encode("utf-8"), zipfile.ZIP_DEFLATED)
    return held.getvalue()


def _sized(data: bytes) -> bytes:
    return struct.pack("<I", len(data)) + data


def data_mashup(queries: list[tuple[str, str]]) -> str:
    """The DataMashup's text: base64 of its version, its package, its permissions, its
    metadata and its permission bindings, each after its length."""
    permissions = ('<?xml version="1.0" encoding="utf-8"?><PermissionList>'
                   "<CanEvaluateFuturePackages>false</CanEvaluateFuturePackages>"
                   "<FirewallEnabled>true</FirewallEnabled></PermissionList>").encode("utf-8")
    metadata_xml = ('<?xml version="1.0" encoding="utf-8"?><LocalPackageMetadataFile>'
                    "<Items /></LocalPackageMetadataFile>").encode("utf-8")
    metadata = struct.pack("<I", 0) + _sized(metadata_xml) + _sized(b"")
    mashup = (struct.pack("<I", 0) + _sized(_package(queries)) + _sized(permissions)
              + _sized(metadata) + _sized(b""))
    return base64.b64encode(mashup).decode("ascii")


def _relationship(rid: str, kind: str, target: str) -> str:
    return (f'<Relationship Id="{rid}" Type="{RELATIONSHIP_TYPES}/{kind}" '
            f'Target="{target}"/>')


def _with_relationships(rels: str, added: list[str]) -> str:
    return rels.replace("</Relationships>", "".join(added) + "</Relationships>")


def _connections(queries: list[tuple[str, str]]) -> str:
    connections = "".join(
        f'<connection id="{number}" keepAlive="1" name={quoteattr("Query - " + name)} '
        f'description={quoteattr(f"Connection to the {name!r} query in the workbook.")} '
        'type="5" refreshedVersion="8" background="1" saveData="1">'
        "<dbPr connection="
        + quoteattr("Provider=Microsoft.Mashup.OleDb.1;Data Source=$Workbook$;"
                    f'Location={name};Extended Properties=""')
        + f" command={quoteattr(f'SELECT * FROM [{name}]')}/></connection>"
        for number, (name, _) in enumerate(queries, 1))
    return f'{HEAD}<connections xmlns="{SPREADSHEET}">{connections}</connections>'


def _query_table(connection: int, columns: list[str]) -> str:
    fields = "".join(f'<queryTableField id="{number}" name={quoteattr(column)} '
                     f'tableColumnId="{number}"/>'
                     for number, column in enumerate(columns, 1))
    return (f'{HEAD}<queryTable xmlns="{SPREADSHEET}" name="ExternalData_{connection}" '
            f'connectionId="{connection}" autoFormatId="16" applyNumberFormats="0" '
            'applyBorderFormats="0" applyFontFormats="0" applyPatternFormats="0" '
            'applyAlignmentFormats="0" applyWidthHeightFormats="0">'
            f'<queryTableRefresh nextId="{len(columns) + 1}">'
            f'<queryTableFields count="{len(columns)}">{fields}</queryTableFields>'
            "</queryTableRefresh></queryTable>")


def _loaded_table(table: str) -> tuple[str, list[str]]:
    """A Table part marked as one a query loads, and its columns' names."""
    columns = re.findall(r'<tableColumn [^>]*name="([^"]*)"', table)
    marked = table.replace("<table ", '<table tableType="queryTable" ', 1)
    pieces = marked.split("<tableColumn ")
    numbered = [f'<tableColumn queryTableFieldId="{number}" ' + piece
                for number, piece in enumerate(pieces[1:], 1)]
    return pieces[0] + "".join(numbered), columns


def with_queries(saved: bytes, queries: list[tuple[str, str]],
                 loads: dict[str, str] | None = None) -> bytes:
    """The workbook `saved`, with `queries` saved in it as Excel saves them, each `(name, M)`;
    `loads` gives the Table each query that loads one loads, by the query's name."""
    loads = loads or {}
    with zipfile.ZipFile(io.BytesIO(saved)) as workbook:
        parts = {name: workbook.read(name) for name in workbook.namelist()}
    text = {name: data.decode("utf-8") for name, data in parts.items()
            if name.endswith((".xml", ".rels"))}
    overrides = [("/xl/connections.xml", TYPES["connections"]),
                 ("/customXml/itemProps1.xml", TYPES["customXmlProps"])]
    text["customXml/item1.xml"] = (
        f'<?xml version="1.0" encoding="utf-8"?><DataMashup xmlns="{MASHUP}">'
        f"{data_mashup(queries)}</DataMashup>")
    text["customXml/itemProps1.xml"] = (
        f'{HEAD}<ds:datastoreItem ds:itemID="{{8F4A43B0-7B1E-4B27-9C2A-6E9A4F9D2C11}}" '
        f'xmlns:ds="{CUSTOM_XML}"><ds:schemaRefs/></ds:datastoreItem>')
    text["customXml/_rels/item1.xml.rels"] = (
        f'{HEAD}<Relationships xmlns="{PACKAGE_RELATIONSHIPS}">'
        + _relationship("rId1", "customXmlProps", "itemProps1.xml") + "</Relationships>")
    text["xl/connections.xml"] = _connections(queries)
    text["xl/_rels/workbook.xml.rels"] = _with_relationships(
        text["xl/_rels/workbook.xml.rels"],
        [_relationship("rIdQueries1", "connections", "connections.xml"),
         _relationship("rIdQueries2", "customXml", "../customXml/item1.xml")])
    tables = {re.search(r'displayName="([^"]*)"', text[name]).group(1): name
              for name in text if re.fullmatch(r"xl/tables/table\d+\.xml", name)}
    connection_of = {name: number for number, (name, _) in enumerate(queries, 1)}
    for number, (query, table) in enumerate(sorted(loads.items()), 1):
        part = tables[table]
        text[part], columns = _loaded_table(text[part])
        query_table = f"xl/queryTables/queryTable{number}.xml"
        text[query_table] = _query_table(connection_of[query], columns)
        overrides.append(("/" + query_table, TYPES["queryTable"]))
        folder, file = part.rsplit("/", 1)
        text[f"{folder}/_rels/{file}.rels"] = (
            f'{HEAD}<Relationships xmlns="{PACKAGE_RELATIONSHIPS}">'
            + _relationship("rId1", "queryTable", f"../queryTables/queryTable{number}.xml")
            + "</Relationships>")
    text["[Content_Types].xml"] = text["[Content_Types].xml"].replace(
        "</Types>", "".join(f'<Override PartName="{name}" ContentType="{kind}"/>'
                            for name, kind in overrides) + "</Types>")
    written = io.BytesIO()
    with zipfile.ZipFile(written, "w", zipfile.ZIP_DEFLATED) as workbook:
        for name in [*parts, *(name for name in text if name not in parts)]:
            workbook.writestr(name, text[name].encode("utf-8") if name in text else parts[name])
    return written.getvalue()
