import html, re, sys
s = open(sys.argv[1], encoding="utf-8").read()
start = s.find(f'id="{sys.argv[2]}"')
end = s.find(f'id="{sys.argv[3]}"') if len(sys.argv) > 3 else -1
t = s[start:end] if end > start else s[start:]
t = re.sub(r'<pre[^>]*>', '\n```\n', t)
t = t.replace('</pre>', '\n```\n')
t = re.sub(r'<[^>]+>', '', t)
print(html.unescape(t))
