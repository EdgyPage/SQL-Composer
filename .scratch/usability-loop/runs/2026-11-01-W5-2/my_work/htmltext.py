import re,html,sys
src=open(sys.argv[1],encoding="utf-8").read()
src=re.sub(r'<pre[^>]*>(.*?)</pre>', lambda m: "\n[CODE]\n"+html.unescape(re.sub(r'<[^>]+>','',m.group(1)))+"\n[/CODE]\n", src, flags=re.S)
src=re.sub(r'<(h[1-6]|p|li|tr|div|ul|ol|table)[^>]*>', '\n', src)
src=re.sub(r'<[^>]+>','',src)
src=html.unescape(src)
src=re.sub(r'\n\s*\n+','\n',src)
open(sys.argv[2],"w",encoding="utf-8").write(src)
