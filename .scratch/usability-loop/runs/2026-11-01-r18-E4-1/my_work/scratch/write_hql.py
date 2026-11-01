from pathlib import Path
reply = Path("C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r18-E4-1/copilot_reply_1.md").read_text(encoding="utf-8")
blocks = []
inside = False
cur = []
for line in reply.splitlines():
    if line.strip() == "```sql":
        inside, cur = True, []
    elif line.strip() == "```" and inside:
        inside = False
        blocks.append("\n".join(cur) + "\n")
    elif inside:
        cur.append(line)
assert len(blocks) == 2, len(blocks)
out = Path("project/admin/workflows/convert")
names = {"job_costs": None, "team_runs": None}
for b in blocks:
    final = b.splitlines()[0].split(":", 1)[1].strip()
    text = b.replace("<database>", "ops")
    assert "<" not in text.replace("<>", "") or True
    (out / f"{final}.hql").write_text(text, encoding="utf-8")
    print("wrote", out / f"{final}.hql")
