import html, re, sys
from html.parser import HTMLParser

src = open(sys.argv[1], encoding="utf-8").read()
start_id, end_id = sys.argv[2], sys.argv[3]
s = src.index(f'id="{start_id}"')
e = src.index(f'id="{end_id}"', s + 1) if end_id != "-" else len(src)
chunk = src[s:e]

class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "li", "h1", "h2", "h3", "h4", "pre", "tr", "div", "br", "ol", "ul"):
            self.out.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
        if tag in ("pre", "p", "li", "h1", "h2", "h3", "h4", "tr"):
            self.out.append("\n")
    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)

p = P()
p.feed(chunk)
text = "".join(p.out)
text = html.unescape(text)
text = re.sub(r"\n\s*\n+", "\n\n", text)
print(text)
