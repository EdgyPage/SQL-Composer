import html, re, sys
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "li", "h1", "h2", "h3", "h4", "pre", "tr", "div", "br", "section"):
            self.out.append("\n")
        if tag == "h2" or tag == "h3":
            self.out.append("\n## ")
        for k, v in attrs:
            if k == "id":
                self.out.append(f"\n[#{v}]")
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
        if tag in ("pre",):
            self.out.append("\n")
    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)

p = P()
p.feed(open(sys.argv[1], encoding="utf-8").read())
text = "".join(p.out)
text = re.sub(r"\n\s*\n+", "\n\n", text)
open(sys.argv[2], "w", encoding="utf-8").write(text)
