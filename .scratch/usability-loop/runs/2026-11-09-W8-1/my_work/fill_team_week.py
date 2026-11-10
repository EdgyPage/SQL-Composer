import json

PATH = r"C:\Users\myfir\AppData\Local\Temp\usability-loop\runs\2026-11-09-W8-1\my_project\scheduled_runs\team_week\team_week.ipynb"

PARAMETERS = '''# parameters
# The values a scheduler passes in, each a name, its type hint and its default. A scheduler
# passes text, which the Build cell reads by the hint, and refuses a value it can't read. The
# hints it reads: datetime.date, int, float, bool, str, each alone, in list[...] or with
# | None, such as list[datetime.date] for "2026-11-01,2026-11-08".
import datetime  # for a datetime.date hint

START_FROM: str = ""  # a table or SELECT to start from, as a failed run prints it; "" sends all
WEEK: datetime.date | None = None  # a day of the week to add up, passed in as text, such as
# "2026-09-16"; the week it is in, Monday to Sunday, is the one added up
'''

SCHEDULED = '''# scheduled
# The Statements this run sends, each by its name: a SELECT's rows come back in results by it.
# Each write is a Table notebook's write_days, for the days of WEEK's week: the writes of the
# two tables mart.team_days reads come first, then mart.team_days's own write, then the SELECT
# week_totals, which adds that week up. The build adds none of its own, since each of these
# tables is written here.
import datetime


def week_days() -> tuple[str, str]:
    """The Monday and the Sunday of WEEK's week, as text, as the logic functions take them."""
    if WEEK is None:
        raise ValueError('team_week needs WEEK, a day of the week to add up, such as '
                         '"2026-09-16", passed in as text.')
    monday = WEEK - datetime.timedelta(days=WEEK.weekday())
    return str(monday), str(monday + datetime.timedelta(days=6))


def statements() -> dict[str, Statement]:
    """What this run sends, by name: the writes of the week's days, then the week's SELECT."""
    first_day, last_day = week_days()
    team_days = project.load("mart.team_days")
    return {
        "job_day_costs": project.load("mart.job_day_costs").write_days(first_day, last_day),
        "job_day_facts": project.load("mart.job_day_facts").write_days(first_day, last_day),
        "team_days": team_days.write_days(first_day, last_day),
        "week_totals": team_days.week_totals(first_day, last_day),
    }
'''

with open(PATH, encoding="utf-8", newline="") as f:
    nb = json.load(f)

code = [c for c in nb["cells"] if c["cell_type"] == "code"]
assert code[0]["metadata"].get("tags") == ["parameters"], code[0]["metadata"]
assert "".join(code[0]["source"]).startswith("# parameters")
assert "".join(code[2]["source"]).startswith("# scheduled")

def lines(text):
    parts = text.split("\n")
    out = [p + "\n" for p in parts[:-1]]
    if parts[-1]:
        out.append(parts[-1])
    return out

code[0]["source"] = lines(PARAMETERS)
code[2]["source"] = lines(SCHEDULED)

text = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(text.replace("\n", "\r\n"))
print("written")
