"""The offline policy: `tools/offline_policy.py` reads the repo's code for anything that could
reach the network, and finds it nowhere but at the sites its `ALLOWED` list reviewed.

The repo is read as the hook and the export read it, through `findings_in`, `scan` and
`stale_entries`; each forbidden form is read from a few lines of text under a repo path.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

import offline_policy
from offline_policy import Allowed, findings_in, scan, stale_entries

ROOT = Path(__file__).resolve().parents[2]
TOOLBOX_FILE = "sqlglot_composer/somewhere.py"
# A made-up site that listens and connects on this computer only, with the entries a review
# would give it.
SITE = "tools/local_server.py"
SITE_ALLOWED = (
    Allowed(SITE, "<module>", "network", "socket", "imports socket, for _launch's listener"),
    Allowed(SITE, "_launch", "network", "socket.create_server",
            "the listener the process connects back to, on 127.0.0.1 only", address="127.0.0.1"),
    Allowed(SITE, "_serve", "network", "multiprocessing.connection.*",
            "connects back to the address its parent sent", address=offline_policy.PASSED_IN),
)


def kinds(text: str, path: str = TOOLBOX_FILE, **options: tuple[Allowed, ...]) -> list[str]:
    return [finding.kind for finding in findings_in(text, path, **options)]


def test_the_repo_reads_clean() -> None:
    assert [str(finding) for finding in scan(ROOT) + stale_entries(ROOT)] == []


def test_a_network_import_in_the_toolbox_is_found() -> None:
    assert kinds("import requests\n") == ["network"]


@pytest.mark.parametrize(("text", "kind"), [
    ("import requests\n", "network"),
    ("from urllib.request import urlopen\n", "network"),
    ("from urllib import request\n", "network"),
    ('import socket\nsocket.create_connection(("example.com", 80))\n', "network"),
    ('import socket as s\ns.create_connection(("example.com", 80))\n', "network"),
    ('from socket import create_connection as dial\ndial(("example.com", 80))\n', "network"),
    ('import importlib\nimportlib.import_module("socket")\n', "network"),
    ("import asyncio\nasyncio.open_connection('example.com', 80)\n", "network"),
    ('__import__("soc" + "ket")\n', "dynamic code"),
    ("import importlib\nimportlib.import_module(name)\n", "dynamic code"),
    ("eval(x)\n", "dynamic code"),
    ("exec(x)\n", "dynamic code"),
    ("run = eval\n", "dynamic code"),
    ("import os\ngetattr(os, name)('ls')\n", "dynamic code"),
    ("import subprocess\n", "process"),
    ("from subprocess import run\n", "process"),
    ("import os\nos.system('curl example.com')\n", "process"),
    ("import os as o\no.execv('/bin/sh', [])\n", "process"),
    ("import ctypes\n", "process"),
    ("import pandas as pd\npd.read_csv(path)\n", "library fetcher"),
    ("import numpy as np\nnp.loadtxt(path)\n", "library fetcher"),
    ('page = "https://x"\n', "URL"),
    ('where = f"ftp://{host}/file"\n', "URL"),
    ('def f():\n    """Run it:\n\n    >>> import requests\n    """\n', "network"),
    ("import pickle\n", "dynamic code"),
    ("import marshal\nmarshal.loads(data)\n", "dynamic code"),
    ("import shelve\n", "dynamic code"),
    ("import zipimport\n", "dynamic code"),
    ("from pickle import loads\nloads(data)\n", "dynamic code"),
    ("import importlib.util\nimportlib.util.spec_from_file_location('m', path)\n",
     "dynamic code"),
    ("from importlib.util import module_from_spec\nmodule_from_spec(spec)\n", "dynamic code"),
    ("from importlib.machinery import SourceFileLoader\n", "dynamic code"),
])
def test_each_forbidden_form_is_found_in_the_toolbox(text: str, kind: str) -> None:
    assert kind in kinds(text)


@pytest.mark.parametrize(("text", "kind"), [
    ("def f(a: __import__('socket')): pass\n", "dynamic code"),
    ("x: eval('1') = 2\n", "dynamic code"),
    ("def f() -> exec('x'): pass\n", "dynamic code"),
    ("try:\n    pass\nexcept eval('Exception'):\n    pass\n", "dynamic code"),
    ("import os\ngetattr(os, 'system')('ls')\n", "process"),
    ("import importlib\ngetattr(importlib, 'import_module')(name)\n", "dynamic code"),
    ("__builtins__.__import__('json')\n", "dynamic code"),
    ("__builtins__['eval'](x)\n", "dynamic code"),
    ("vars(__builtins__)['eval'](x)\n", "dynamic code"),
    ("import sys\nsys.modules['os'].system('ls')\n", "process"),
    ("import os\nos.__dict__['system']('ls')\n", "process"),
    ("import importlib\nimportlib.import_module('os').system('ls')\n", "process"),
    ("import importlib\nimportlib.import_module('soc' + 'ket')\n", "network"),
    ("from os import *\nsystem('ls')\n", "dynamic code"),
    ("import multiprocessing\nmultiprocessing.Process(target=f).start()\n", "process"),
    ("from concurrent.futures import ProcessPoolExecutor\n", "process"),
    ("import pandas as pd\npd.io.parsers.read_csv(path)\n", "library fetcher"),
    ("import numpy as np\nnp.lib.npyio.loadtxt(path)\n", "library fetcher"),
    ("page = 'https:' + '//x'\n", "URL"),
])
def test_a_disguised_form_is_found_too(text: str, kind: str) -> None:
    assert kind in kinds(text)


def test_a_call_named_in_capitals_is_no_constant() -> None:
    found = findings_in("import ctypes\n\ndef f():\n    ctypes.CDLL('x')\n", TOOLBOX_FILE)
    assert [finding.name for finding in found] == ["ctypes", "ctypes.CDLL"]


def test_a_name_from_a_network_module_that_reaches_nothing_is_not_found() -> None:
    assert kinds("from http import HTTPStatus\n") == []
    text = "import subprocess\n\ndef f(p: subprocess.Popen) -> None:\n    pass\n"
    assert kinds(text) == ["process"]


def test_a_url_in_a_docstring_or_a_comment_is_prose() -> None:
    text = ('"""See https://x for more."""\n\n# and https://y\n'
            'def f():\n    """And https://z."""\n')
    assert kinds(text) == []


def test_the_toolbox_own_imports_are_not_found() -> None:
    text = ("import os\nimport urllib.parse\nimport pandas as pd\nfrom . import engine\n"
            "from .engine import run_query\npd.DataFrame(rows)\nos.path.join('a', 'b')\n"
            "with open(path) as requests:\n    requests.read()\n")
    assert kinds(text) == []


def test_each_finding_says_where_it_is_and_what_it_is() -> None:
    [finding] = findings_in("import os\n\ndef f():\n    os.system('ls')\n", TOOLBOX_FILE)
    assert str(finding) == f"{TOOLBOX_FILE}:4 process: os.system('ls')"
    assert (finding.function, finding.name) == ("f", "os.system")


def test_a_file_that_doesnt_parse_cant_be_read() -> None:
    assert kinds("def f(:\n") == ["unreadable"]


def test_a_file_that_declares_an_encoding_other_than_utf_8_cant_be_read() -> None:
    # Python reads this one in UTF-7, where `+AAo-` is a new line before `import requests`.
    assert kinds("# coding: utf-7\nx = 1 #+AAo-import requests\n") == ["unreadable"]
    assert kinds("#!/usr/bin/env python\n# -*- coding: latin-1 -*-\nx = 1\n") == ["unreadable"]
    assert kinds("# -*- coding: utf-8 -*-\nx = 1\n") == []


def test_a_windows_script_is_read_as_python() -> None:
    assert kinds("import requests\n", "sqlglot_composer/x.pyw") == ["network"]


def test_no_folder_inside_the_toolbox_or_user_copied_code_is_skipped(tmp_path: Path) -> None:
    # A `.venv`-like folder, or one named like a cache, could otherwise hold code a Toolbox
    # file imports unread.
    for folder in ("sqlglot_composer/a", "example_projects/node_modules",
                   "sqlglot_composer/.scratch"):
        (tmp_path / folder).mkdir(parents=True)
        (tmp_path / folder / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
        (tmp_path / folder / "x.py").write_text("import requests\n", encoding="utf-8")
    (tmp_path / "tools" / ".venv").mkdir(parents=True)
    (tmp_path / "tools" / ".venv" / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
    (tmp_path / "tools" / ".venv" / "x.py").write_text("import requests\n", encoding="utf-8")
    assert sorted(finding.path for finding in scan(tmp_path)) == [
        "example_projects/node_modules/x.py", "sqlglot_composer/.scratch/x.py",
        "sqlglot_composer/a/x.py"]


def test_a_template_is_read_with_its_placeholders_as_names() -> None:
    text = "import <MODULE>\nimport requests\nDAY = <DAY>\n"
    assert kinds(text, "example_projects/starter/x.py") == ["network"]


@pytest.mark.parametrize("text", [
    '<script src="https://example.com/x.js"></script>',
    '<link rel="stylesheet" href="x.css">',
    "<style>@import 'x.css';</style>",
    "<style>body { background: url(x.png); }</style>",
    "<script>fetch('/data')</script>",
    "<script>new XMLHttpRequest()</script>",
    "<script>new WebSocket(where)</script>",
    "<script>navigator.sendBeacon(where)</script>",
    "<iframe></iframe>",
    '<a href="http://example.com">x</a>',
    '<a href="//example.com/x">x</a>',
    '<a href="javascript:run()">x</a>',
    '<img alt="" srcset="x.png">',
    '<p style="background-image: url(data:image/png;base64,AAAA)"></p>',
    '<form action="/send" method="post"></form>',
    "<script>window.open(where)</script>",
    "<script>window.location = where</script>",
    "<script>location.href = where</script>",
    "<script>location.assign(where)</script>",
    '<meta http-equiv="refresh" content="0; url=x">',
    "<script>importScripts('x.js')</script>",
    "<script>eval(text)</script>",
    "<script>new Function(text)()</script>",
    "<script>setTimeout('run()', 10)</script>",
])
def test_a_page_that_reaches_outside_itself_is_found(text: str) -> None:
    assert offline_policy.external_references(text) != []
    assert "page reference" in kinds(text, "sqlglot_composer/examples.html")


def test_a_page_that_reaches_nothing_has_no_references() -> None:
    page = ("<!doctype html><style>p { color: red; }</style><p>parse_url(x)</p>"
            "<script>navigator.clipboard.writeText(text)</script>"
            '<a href="#start">x</a><a href="examples.html#run">y</a>'
            "<pre>Table(location=&quot;/data&quot;)</pre>"
            "<script>const view = new URLSearchParams(location.search);"
            " setTimeout(draw, 10); history.replaceState(null, '', '?' + view)</script>")
    assert offline_policy.external_references(page) == []


def test_a_reference_says_its_line() -> None:
    assert offline_policy.external_references("<p>\n<script>fetch('/x')</script>") == [
        "line 2: fetch("]


def test_markdown_is_read_as_a_page_only_when_asked() -> None:
    # The hook and the repo's scan leave Markdown alone, so notes may cite their sources; the
    # export reads the Clean tree's Markdown as pages, since a preview loads what it embeds.
    text = 'See the picture.\n<img src="https://example.com/x.png">\n'
    assert findings_in(text, "example_projects/README.md") == []
    found = offline_policy.page_findings(text, "example_projects/README.md")
    assert [str(finding) for finding in found] == [
        'example_projects/README.md:2 page reference: <img src="https://example.com/x.png">'] * 2


def test_user_copied_code_may_hold_nothing_at_all() -> None:
    entry = Allowed("example_projects/starter/x.py", "<module>", "network", "socket",
                    "a reason")
    for folder in ("example_projects", "worked_examples"):
        path = f"{folder}/starter/x.py"
        assert kinds("import socket\n", path) == ["network"]
        assert kinds('page = "https://x"\n', path) == ["URL"]
    assert kinds("import socket\n", "example_projects/starter/x.py",
                 allowed=(entry,)) == ["network"]
    assert [finding.kind for finding in stale_entries(ROOT, (entry,))] == ["stale entry"]


def test_an_allowed_import_is_found_anywhere_else() -> None:
    assert kinds("import socket\n", SITE, allowed=SITE_ALLOWED) == []
    assert kinds("import socket\n", "tools/elsewhere.py", allowed=SITE_ALLOWED) == ["network"]
    assert kinds("import socket\n", "example_projects/starter/daily_pipeline.py",
                 allowed=SITE_ALLOWED) == ["network"]


def test_maintainer_code_may_start_processes_only_where_allowed_and_hold_urls() -> None:
    assert kinds("import requests\n", "tests/test_x.py") == ["network"]
    assert kinds("import subprocess\n", "tests/test_x.py") == ["process"]
    assert kinds("import subprocess\n", "tests/repo/test_hooks.py") == []
    assert kinds('assert "https://" not in page\n', "tests/test_x.py") == []


def test_the_allowed_socket_is_refused_off_127_0_0_1() -> None:
    def launching_on(address: str) -> str:
        return f"import socket\n\ndef _launch():\n    socket.create_server(({address}, 0))\n"

    assert kinds(launching_on('"127.0.0.1"'), SITE, allowed=SITE_ALLOWED) == []
    [finding] = findings_in(launching_on('"0.0.0.0"'), SITE, allowed=SITE_ALLOWED)
    assert (finding.kind, finding.name, finding.address) == (
        "network", "socket.create_server", "0.0.0.0")
    assert kinds(launching_on("host"), SITE, allowed=SITE_ALLOWED) == ["network"]


def test_an_allowed_client_connects_only_to_the_address_it_is_sent() -> None:
    def serving(address: str) -> str:
        return ("def _serve():\n    from multiprocessing.connection import Client\n"
                f"    connection = Client({address}, authkey=key)\n")

    assert kinds(serving('tuple(config["address"])'), SITE, allowed=SITE_ALLOWED) == []
    assert kinds(serving('("example.com", 80)'), SITE, allowed=SITE_ALLOWED) == ["network"]
    # Kept to be called later, the listener's address could be anything.
    assert kinds("import socket\n\ndef _launch():\n    listen = socket.create_server\n",
                 SITE, allowed=SITE_ALLOWED) == ["network"]


def test_an_allowed_entry_that_matches_nothing_is_stale() -> None:
    entry = Allowed("tools/export_clean.py", "_nowhere", "network", "socket.create_connection",
                    "a reason")
    [stale] = stale_entries(ROOT, (entry,))
    assert (stale.path, stale.kind) == ("tools/export_clean.py", "stale entry")
    assert "matches nothing" in stale.code


def test_every_allowed_entry_gives_its_reason() -> None:
    assert all(entry.reason.strip() for entry in offline_policy.ALLOWED)


def test_a_notebook_s_code_cells_and_shell_lines_are_read() -> None:
    notebook = ('{"cells": [{"cell_type": "markdown", "source": ["https://x"]},'
                ' {"cell_type": "code", "source": ["!curl example.com\\n", "import requests"]}]}')
    assert kinds(notebook, "example_projects/starter/start.ipynb") == ["process", "network"]


def test_a_path_that_isnt_there_is_said_so(tmp_path: Path) -> None:
    assert [finding.kind for finding in scan(tmp_path, ["nowhere.py"])] == ["unreadable"]


def test_the_command_line_prints_each_finding_and_fails(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    spoiled = tmp_path / "spoiled.py"
    spoiled.write_text("import json\nimport requests\n", encoding="utf-8")
    assert offline_policy.main(["offline_policy.py", str(spoiled)]) == 1
    assert capsys.readouterr().out.strip().endswith(":2 network: import requests")
    clean = tmp_path / "clean.py"
    clean.write_text("import json\n", encoding="utf-8")
    assert offline_policy.main(["offline_policy.py", str(clean)]) == 0


# --- A workbook ------------------------------------------------------------------------------------

WORKBOOK_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
MACRO_TYPE = "application/vnd.ms-excel.sheet.macroEnabled.main+xml"


def workbook(tmp_path: Path, parts: dict[str, str | bytes], main_type: str = WORKBOOK_TYPE,
             path: str = "copilot/w.xlsx") -> Path:
    """A workbook at `path` under `tmp_path`, holding the parts every workbook has and `parts`."""
    file = tmp_path / path
    file.parent.mkdir(parents=True, exist_ok=True)
    types = (f'<Types><Override PartName="/xl/workbook.xml" ContentType="{main_type}"/>'
             "</Types>")
    with zipfile.ZipFile(file, "w") as written:
        written.writestr("[Content_Types].xml", types)
        written.writestr("xl/workbook.xml", "<workbook><sheets/></workbook>")
        for name, data in parts.items():
            written.writestr(name, data)
    return file


def test_a_workbook_that_reaches_nothing_has_no_findings(tmp_path: Path) -> None:
    workbook(tmp_path, {"xl/worksheets/sheet1.xml": "<worksheet/>",
                        "xl/tables/table1.xml": '<table name="Keys" ref="A1:B2"/>'})
    assert scan(tmp_path) == []


@pytest.mark.parametrize(("parts", "main_type", "kind"), [
    ({"xl/vbaProject.bin": b"Attribute VB_Name"}, WORKBOOK_TYPE, "dynamic code"),
    ({}, MACRO_TYPE, "dynamic code"),
    ({"xl/embeddings/oleObject1.bin": b"x"}, WORKBOOK_TYPE, "dynamic code"),
    ({"xl/activeX/activeX1.xml": "<ax/>"}, WORKBOOK_TYPE, "dynamic code"),
    ({"xl/connections.xml": "<connections/>"}, WORKBOOK_TYPE, "network"),
    ({"xl/queryTables/queryTable1.xml": "<queryTable/>"}, WORKBOOK_TYPE, "network"),
    ({"xl/externalLinks/externalLink1.xml": "<externalLink/>"}, WORKBOOK_TYPE, "network"),
    ({"customXml/item1.xml": "<DataMashup/>"}, WORKBOOK_TYPE, "network"),
    ({"xl/worksheets/_rels/sheet1.xml.rels":
      '<Relationships><Relationship Id="rId1" Target="https://example.com" '
      'TargetMode="External"/></Relationships>'}, WORKBOOK_TYPE, "network"),
    ({"xl/worksheets/_rels/sheet1.xml.rels":
      "<Relationships><Relationship Id='rId1' Target='x' TargetMode = 'External'/>"
      "</Relationships>"}, WORKBOOK_TYPE, "network"),
    ({"xl/worksheets/sheet1.xml":
      '<worksheet><c r="A1"><f>WEBSERVICE("x")</f></c></worksheet>'}, WORKBOOK_TYPE, "network"),
    ({"xl/sharedStrings.xml": "<sst><si><t>see https://example.com</t></si></sst>"},
     WORKBOOK_TYPE, "URL"),
])
def test_a_workbook_with_a_macro_a_connection_or_a_link_out_is_found(
        tmp_path: Path, parts: dict[str, str | bytes], main_type: str, kind: str) -> None:
    workbook(tmp_path, parts, main_type)
    found = scan(tmp_path)
    assert [finding.kind for finding in found] == [kind]
    assert found[0].path == "copilot/w.xlsx"


def test_a_workbook_is_read_in_any_folder(tmp_path: Path) -> None:
    workbook(tmp_path, {"xl/connections.xml": "<connections/>"}, path="tools/w.xlsx")
    assert [finding.kind for finding in scan(tmp_path)] == ["network"]


def test_a_workbook_that_isnt_one_cant_be_read(tmp_path: Path) -> None:
    (tmp_path / "w.xlsx").write_bytes(b"not a zip")
    assert [finding.kind for finding in scan(tmp_path)] == ["unreadable"]
