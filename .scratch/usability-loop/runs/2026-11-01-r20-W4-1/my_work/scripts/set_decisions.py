from pathlib import Path
import json

nb = Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r20-W4-1\my_work\my_project\admin\workflows\references\references.ipynb")
raw = nb.read_bytes()
text = raw.decode("utf-8")
data = json.loads(text)
# round-trip check: the file must come back byte-for-byte before we change it
rebuilt = json.dumps(data, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n"
print("round trip identical:", rebuilt == text)
if rebuilt != text:
    raise SystemExit("round trip differs; not editing")
code = [c for c in data["cells"] if c["cell_type"] == "code"]
decisions = code[2]
assert "".join(decisions["source"]).startswith("DECISIONS = {}"), "not the decisions cell"
decisions["source"] = [
    'DECISIONS = {"ops.jobs": {"key": ["job_id"]}, "ops.run_alerts": {"key": ["alert_id"]}}\n'.rstrip("\n")
]
nb.write_bytes((json.dumps(data, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))
print("".join(json.loads(nb.read_text(encoding="utf-8"))["cells"][4]["source"]) if False else "".join(
    [c for c in json.loads(nb.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code"][2]["source"]))
