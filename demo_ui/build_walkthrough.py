"""Compile the authored worked example into an offline HTML asset."""
from pathlib import Path
from html import escape
import json,re
root=Path(__file__).resolve().parent
lines=(root/'GIBS_WORKED_EXAMPLE.md').read_text().splitlines()
html=[];paragraph=[];code=[];in_code=False;table=[]
def inline(s):return re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',escape(s))
def flush():
    if paragraph:html.append('<p>'+inline(' '.join(paragraph))+'</p>');paragraph.clear()
def flush_table():
    if not table:return
    rows=[row for row in table if not all(set(cell.strip())<=set('-: ') for cell in row)]
    html.append('<div class="table-scroll"><table class="metrics-table"><thead><tr>'+''.join('<th>'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>')
    for row in rows[1:]:html.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>')
    html.append('</tbody></table></div>');table.clear()
for line in lines:
    if line.startswith('```'):
        flush();flush_table()
        if in_code:html.append('<pre class="code-block">'+escape('\n'.join(code))+'</pre>');code=[]
        in_code=not in_code;continue
    if in_code:code.append(line);continue
    if line.startswith('|'):flush();table.append([c.strip() for c in line.strip().strip('|').split('|')]);continue
    flush_table()
    if not line.strip():flush();continue
    if line.startswith('## '):flush();html.append('<h3>'+inline(line[3:])+'</h3>');continue
    if line.startswith('# '):flush();html.append('<h2>'+inline(line[2:])+'</h2>');continue
    paragraph.append(line)
flush();flush_table();assert not in_code
out=root/'dist/assets/worked-example.js'
out.write_text('window.GIBS_WALKTHROUGH_HTML='+json.dumps(''.join(html),ensure_ascii=False)+';\n')
print(out)
