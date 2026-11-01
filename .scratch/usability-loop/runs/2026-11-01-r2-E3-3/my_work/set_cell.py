"""set_cell.py NOTEBOOK INDEX TEXTFILE: replace the source of a notebook's cell with a file's text."""
import json, sys
nb_path, index, text_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
nb = json.load(open(nb_path, encoding='utf-8'))
text = open(text_path, encoding='utf-8').read()
lines = text.splitlines(keepends=True)
nb['cells'][index]['source'] = lines
json.dump(nb, open(nb_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('set cell', index, 'of', nb_path)
