"""Save Power Queries into a workbook the way Excel saves them, for dev's tests and evaluations.

openpyxl writes no Power Query, so a workbook built with it holds none. This adds them to the
saved file, as Excel does ([MS-QDEFF]):
- a `customXml` item, the DataMashup: base64 of a version, then a zip whose
  Formulas/Section1.m holds every query's M, then the package's permissions and metadata;
- a connection for each query in `xl/connections.xml`, naming the query;
- for each query that loads a Table, a query table beside the Table, which names that
  connection.

`copilot/workbook_text.py` reads them back, as it reads a workbook Excel saved. Excel 16 opens
each fixture built this way (ticket 19 opened them through COM); no test can run Excel.
"""

from __future__ import annotations

import base64
import io
import re
import struct
import uuid
import zipfile
from xml.sax.saxutils import escape, quoteattr, unescape

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


# The namespaces Excel declares on the mashup's own XML documents.
XSD_XSI = ('xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
# An empty zip, its end record alone: what Excel saves after the metadata's XML.
EMPTY_ZIP = b"PK\x05\x06" + bytes(18)


def _package(queries: list[tuple[str, str]]) -> bytes:
    """The zip of the mashup's parts, as Excel writes it: its configuration, its content types
    and its M, each XML part with a byte order mark. The queries' items are the metadata's
    (`_metadata`): Excel finds no query in a package whose Package.xml lists them (ticket
    19)."""
    files = {
        "Config/Package.xml": (
            f'<?xml version="1.0" encoding="utf-8"?><Package {XSD_XSI}>'
            "<Version>2.160.729.0</Version><MinVersion>2.21.0.0</MinVersion>"
            "<Culture>en-US</Culture></Package>").encode("utf-8-sig"),
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="utf-8"?><Types xmlns="'
            f'{CONTENT_TYPES}"><Default Extension="xml" ContentType="text/xml" />'
            '<Default Extension="m" ContentType="application/x-ms-m" /></Types>'
        ).encode("utf-8-sig"),
        "Formulas/Section1.m": section(queries).encode("utf-8"),
    }
    held = io.BytesIO()
    with zipfile.ZipFile(held, "w", zipfile.ZIP_DEFLATED) as package:
        for name, data in files.items():
            # A fixed time and system, so a package built twice, on any computer, holds the
            # same bytes: ZipInfo records the system it was made on.
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 0
            package.writestr(entry, data, zipfile.ZIP_DEFLATED)
    return held.getvalue()


def _metadata(queries: list[tuple[str, str]], loads: dict[str, str]) -> bytes:
    """The mashup's metadata as Excel writes it: a version, then its XML, an item for every
    formula and one for each query, saying whether it fills a Table (`loads` names the Table
    of each query that loads one) or is a connection only, with its QueryID, a uuid5 of its
    name, so a workbook built twice holds the same one; then an empty zip."""
    items = ["<Item><ItemLocation><ItemType>AllFormulas</ItemType><ItemPath /></ItemLocation>"
             "<StableEntries /></Item>"]
    for name, _ in queries:
        table = loads.get(name)
        if table:
            fill = ('<Entry Type="FillEnabled" Value="l1" /><Entry Type="FillObjectType" '
                    'Value="sTable" /><Entry Type="FillToDataModelEnabled" Value="l0" />'
                    f'<Entry Type="FillTarget" Value="s{escape(table)}" />')
        else:
            fill = ('<Entry Type="FillEnabled" Value="l0" /><Entry Type="FillObjectType" '
                    'Value="sConnectionOnly" /><Entry Type="FillToDataModelEnabled" '
                    'Value="l0" />')
        query_id = uuid.uuid5(uuid.NAMESPACE_URL, f"sqlglot-composer:query:{name}")
        items.append(f"<Item><ItemLocation><ItemType>Formula</ItemType><ItemPath>Section1/"
                     f"{escape(name)}</ItemPath></ItemLocation><StableEntries>"
                     f'<Entry Type="IsPrivate" Value="l0" />{fill}'
                     f'<Entry Type="QueryID" Value="s{query_id}" /></StableEntries></Item>')
    xml = (f'<?xml version="1.0" encoding="utf-8"?><LocalPackageMetadataFile {XSD_XSI}>'
           f'<Items>{"".join(items)}</Items></LocalPackageMetadataFile>').encode("utf-8-sig")
    return struct.pack("<I", 0) + _sized(xml) + _sized(EMPTY_ZIP)


def _sized(data: bytes) -> bytes:
    return struct.pack("<I", len(data)) + data


def data_mashup(queries: list[tuple[str, str]],
                loads: dict[str, str] | None = None) -> str:
    """The DataMashup's text: base64 of its version, its package, its permissions, its
    metadata and its permission bindings, each after its length; `loads` names the Table each
    query that loads one loads. The bindings are left empty: Excel reads the queries
    without them."""
    permissions = (f'<?xml version="1.0" encoding="utf-8"?><PermissionList {XSD_XSI}>'
                   "<CanEvaluateFuturePackages>false</CanEvaluateFuturePackages>"
                   "<FirewallEnabled>true</FirewallEnabled></PermissionList>"
                   ).encode("utf-8-sig")
    mashup = (struct.pack("<I", 0) + _sized(_package(queries)) + _sized(permissions)
              + _sized(_metadata(queries, loads or {})) + _sized(b""))
    return base64.b64encode(mashup).decode("ascii")


def mashup_sections(mashup_text: str) -> list[bytes]:
    """The four sections of the DataMashup whose text `data_mashup` gives ([MS-QDEFF] 2.2):
    its package, permissions, metadata and permission bindings, each after its length, after
    a version."""
    raw = base64.b64decode(mashup_text)
    sections, at = [], 4
    for _ in range(4):
        size = struct.unpack("<I", raw[at:at + 4])[0]
        sections.append(raw[at + 4:at + 4 + size])
        at += 4 + size
    return sections


def relationship(rid: str, kind: str, target: str) -> str:
    """A part's relationship `rid` to `target`, of the type `kind` under RELATIONSHIP_TYPES."""
    return (f'<Relationship Id="{rid}" Type="{RELATIONSHIP_TYPES}/{kind}" '
            f'Target="{target}"/>')


def with_relationships(rels: str, added: list[str]) -> str:
    """A part's relationships `rels`, with each relationship `added` after them."""
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
    """A Table part marked as one a query loads, and its columns' names: each column names its
    query table field and has a uniqueName, its id, as Excel saves it (Excel refuses a query's
    Table without them, ticket 19)."""
    columns = re.findall(r'<tableColumn [^>]*name="([^"]*)"', table)
    marked = table.replace("<table ", '<table tableType="queryTable" ', 1)
    pieces = marked.split("<tableColumn ")
    numbered = []
    for number, piece in enumerate(pieces[1:], 1):
        column_id = re.search(r'id="(\d+)"', piece).group(1)
        numbered.append(f'<tableColumn queryTableFieldId="{number}" uniqueName="{column_id}" '
                        + piece)
    return pieces[0] + "".join(numbered), columns


def with_defined_names(workbook_xml: str, names: str) -> str:
    """The workbook part `workbook_xml` with `names`, the XML of its defined names, in its one
    list: openpyxl's empty `<definedNames />`, the end of a list it holds, or a new list
    before `<calcPr`. Excel refuses a workbook with two lists (ticket 19)."""
    if not names:
        return workbook_xml
    empty_list = re.search(r"<definedNames\s*/>", workbook_xml)
    if empty_list:
        return workbook_xml.replace(empty_list.group(), f"<definedNames>{names}</definedNames>",
                                    1)
    if "</definedNames>" in workbook_xml:
        return workbook_xml.replace("</definedNames>", names + "</definedNames>", 1)
    return workbook_xml.replace("<calcPr", f"<definedNames>{names}</definedNames><calcPr", 1)


def _part_of(target: str, beside: str) -> str:
    """The part a relationship's `target` names, from the part `beside` whose relationships
    hold it: openpyxl writes targets from the package's top, Excel beside their part."""
    if target.startswith("/"):
        return target[1:]
    folder = beside.rsplit("/", 1)[0].split("/")
    for step in target.split("/"):
        if step == "..":
            folder.pop()
        else:
            folder.append(step)
    return "/".join(folder)


def _sheet_holding(text: dict[str, str], table_part: str) -> tuple[int, str]:
    """The place among the workbook's sheets, and the name, of the sheet whose Table is
    `table_part`."""
    rels = text["xl/_rels/workbook.xml.rels"]
    sheets = re.findall(r'<sheet [^>]*name="([^"]*)"[^>]*r:id="([^"]*)"',
                        text["xl/workbook.xml"])
    for index, (name, rid) in enumerate(sheets):
        target = re.search(rf'<Relationship [^>]*Target="([^"]*)"[^>]*Id="{rid}"|'
                           rf'<Relationship [^>]*Id="{rid}"[^>]*Target="([^"]*)"', rels)
        sheet = _part_of(target.group(1) or target.group(2), "xl/workbook.xml")
        folder, file = sheet.rsplit("/", 1)
        sheet_rels = text.get(f"{folder}/_rels/{file}.rels", "")
        tables = [_part_of(found, sheet) for found in re.findall(r'Target="([^"]*)"',
                                                                  sheet_rels)]
        if table_part in tables:
            # The workbook part holds the name as XML: &amp; for &.
            return index, unescape(name, {"&quot;": '"', "&apos;": "'"})
    raise ValueError(f"No sheet holds the Table part {table_part}.")


def _range_on(sheet: str, ref: str) -> str:
    """The range `ref`, such as A1:C6, on the sheet `sheet`, as a defined name holds it:
    absolute, the sheet quoted unless its name is plain and no cell's."""
    cells = ":".join(re.sub(r"([A-Z]+)(\d+)", r"$\1$\2", end) for end in ref.split(":"))
    plain = re.fullmatch(r"[A-Za-z_][\w.]*", sheet)
    like_a_cell = re.fullmatch(r"[A-Za-z]{1,3}\d+|[Rr]\d*[Cc]\d*", sheet)
    if plain and not like_a_cell:
        return f"{sheet}!{cells}"
    quoted = sheet.replace("'", "''")
    return f"'{quoted}'!{cells}"


def _query_table_defined_name(text: dict[str, str], table_part: str, connection: int) -> str:
    """The XML of the hidden defined name Excel saves for the query table filling
    `table_part`: the query table's own name, local to the sheet the Table is on, over the
    Table's range."""
    index, sheet = _sheet_holding(text, table_part)
    ref = re.search(r'<table [^>]*ref="([^"]*)"', text[table_part]).group(1)
    return (f'<definedName name="ExternalData_{connection}" localSheetId="{index}" '
            f'hidden="1">{escape(_range_on(sheet, ref))}</definedName>')


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
        f"{data_mashup(queries, loads)}</DataMashup>")
    text["customXml/itemProps1.xml"] = (
        f'{HEAD}<ds:datastoreItem ds:itemID="{{8F4A43B0-7B1E-4B27-9C2A-6E9A4F9D2C11}}" '
        f'xmlns:ds="{CUSTOM_XML}"><ds:schemaRefs/></ds:datastoreItem>')
    text["customXml/_rels/item1.xml.rels"] = (
        f'{HEAD}<Relationships xmlns="{PACKAGE_RELATIONSHIPS}">'
        + relationship("rId1", "customXmlProps", "itemProps1.xml") + "</Relationships>")
    text["xl/connections.xml"] = _connections(queries)
    text["xl/_rels/workbook.xml.rels"] = with_relationships(
        text["xl/_rels/workbook.xml.rels"],
        [relationship("rIdQueries1", "connections", "connections.xml"),
         relationship("rIdQueries2", "customXml", "../customXml/item1.xml")])
    tables = {re.search(r'displayName="([^"]*)"', text[name]).group(1): name
              for name in text if re.fullmatch(r"xl/tables/table\d+\.xml", name)}
    connection_of = {name: number for number, (name, _) in enumerate(queries, 1)}
    defined_names = []
    for number, (query, table) in enumerate(sorted(loads.items()), 1):
        part = tables[table]
        defined_names.append(_query_table_defined_name(text, part, connection_of[query]))
        text[part], columns = _loaded_table(text[part])
        query_table = f"xl/queryTables/queryTable{number}.xml"
        text[query_table] = _query_table(connection_of[query], columns)
        overrides.append(("/" + query_table, TYPES["queryTable"]))
        folder, file = part.rsplit("/", 1)
        text[f"{folder}/_rels/{file}.rels"] = (
            f'{HEAD}<Relationships xmlns="{PACKAGE_RELATIONSHIPS}">'
            + relationship("rId1", "queryTable", f"../queryTables/queryTable{number}.xml")
            + "</Relationships>")
    text["xl/workbook.xml"] = with_defined_names(text["xl/workbook.xml"],
                                                 "".join(defined_names))
    text["[Content_Types].xml"] = text["[Content_Types].xml"].replace(
        "</Types>", "".join(f'<Override PartName="{name}" ContentType="{kind}"/>'
                            for name, kind in overrides) + "</Types>")
    written = io.BytesIO()
    with zipfile.ZipFile(written, "w", zipfile.ZIP_DEFLATED) as workbook:
        for name in [*parts, *(name for name in text if name not in parts)]:
            workbook.writestr(name, text[name].encode("utf-8") if name in text else parts[name])
    return written.getvalue()
