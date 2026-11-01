import html, re, sys
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "li", "h1", "h2", "h3", "h4", "pre", "div", "tr", "br", "ol", "ul", "section"):
            self.out.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)

path, anchor = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
start = text.find('id="%s"' % anchor)
if start < 0:
    sys.exit("no anchor " + anchor)
# next top-level section after the anchor
m = re.search(r'<(section|h2)[^>]*id="(?!%s")[a-z_]+"' % anchor, text[start + 10:])
end = start + 10 + m.start() if m else len(text)
p = P()
p.feed(text[start:end])
out = "".join(p.out)
out = re.sub(r"\n\s*\n+", "\n\n", out)
print(out)
