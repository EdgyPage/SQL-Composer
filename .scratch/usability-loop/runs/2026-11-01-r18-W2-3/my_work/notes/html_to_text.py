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
        if tag in ("p", "li", "h1", "h2", "h3", "h4", "tr", "div", "br", "pre"):
            self.out.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)

src = open(sys.argv[1], encoding="utf-8").read()
p = P()
p.feed(src)
text = "".join(p.out)
text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r"\n\s*\n+", "\n\n", text)
sys.stdout.write(html.unescape(text))
