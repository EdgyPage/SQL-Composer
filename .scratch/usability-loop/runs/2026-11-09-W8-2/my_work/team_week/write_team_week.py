import json, sys
p = sys.argv[1]
raw = open(p, "rb").read().decode("utf-8")
crlf = "\r\n" in raw
nb = json.loads(raw)

PARAMETERS = '''# parameters
# The values a scheduler passes in, each a name, its type hint and its default. A scheduler
# passes text, which the Build cell reads by the hint, and refuses a value it can't read. The
# hints it reads: datetime.date, int, float, bool, str, each alone, in list[...] or with
# | None, such as list[datetime.date] for "2026-11-01,2026-11-08".
import datetime  # for a datetime.date hint

START_FROM: str = ""  # a table or SELECT to start from, as a failed run prints it; "" sends all
WEEK: datetime.date  # a day of the week to add up, such as "2026-09-16", passed in as text
'''

SCHEDULED = '''# scheduled
# The Statements this run sends, each by its name, for WEEK's week, Monday to Sunday. Each
# table mart.team_days reads is written for those days first, from its own logic, then
# mart.team_days for them, then week_totals gives that week's rows back by its name.
import datetime


def week_days() -> tuple[str, str]:
    """The Monday that starts WEEK's week and the Sunday that ends it, each as text, such as
    "2026-09-14", as the logic functions take their days."""
    monday = WEEK - datetime.timedelta(days=WEEK.weekday())
    return str(monday), str(monday + datetime.timedelta(days=6))


def statements() -> dict[str, Statement]:
    """What this run sends, by name: the writes of the week's days, then week_totals."""
    first_day, last_day = week_days()
    return {
        "job_day_facts": project.load("mart.job_day_facts").write_days(first_day, last_day),
        "job_day_costs": project.load("mart.job_day_costs").write_days(first_day, last_day),
        "team_days": project.load("mart.team_days").write_days(first_day, last_day),
        "week_totals": project.load("mart.team_days").week_totals(first_day, last_day),
    }
'''

def lines(text):
    return text.splitlines(keepends=True)

done = {"parameters": 0, "scheduled": 0}
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    first = "".join(cell["source"]).split("\n", 1)[0]
    if first == "# parameters":
        cell["source"] = lines(PARAMETERS)
        done["parameters"] += 1
    elif first == "# scheduled":
        cell["source"] = lines(SCHEDULED)
        done["scheduled"] += 1
assert done == {"parameters": 1, "scheduled": 1}, done

out = json.dumps(nb, indent=1, ensure_ascii=False)
if raw.endswith("\n"):
    out += "\n"
if crlf:
    out = out.replace("\r\n", "\n").replace("\n", "\r\n")
open(p, "wb").write(out.encode("utf-8"))
print("ok, crlf:", crlf)
