import pathlib
src = pathlib.Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E2-2\my_work\copilot_answer_1.md").read_text(encoding="utf-8")
start = src.index("```sql\n") + len("```sql\n")
end = src.index("```", start)
hive = src[start:end].replace("<database>", "ops")
out = pathlib.Path(r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-01-r2-E2-2\my_work\team_report.hql")
out.write_text(hive, encoding="utf-8")
print(hive)
