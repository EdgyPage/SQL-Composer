import zipfile, re
path = "C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-01-r3-E2-2/my_work/team_report_formula.xlsx"
with zipfile.ZipFile(path) as z:
    for name in sorted(z.namelist()):
        if name.startswith("xl/tables/"):
            x = z.read(name).decode("utf8")
            print(name, re.findall(r'<table [^>]*displayName="[^"]+"[^>]*ref="[^"]+"', x)[:1])
            print("   columns:", re.findall(r'<tableColumn [^>]*name="([^"]+)"', x))
    print("sheet files:", [n for n in z.namelist() if n.startswith("xl/worksheets/")])
