from pathlib import Path
from bs4 import BeautifulSoup
import re
p=Path('guia/index.html')
s=p.read_text(encoding='utf-8').replace('Copia los prompts de uno en uno.', 'Escribe los prompts de uno en uno.')
soup=BeautifulSoup(s,'html.parser')
original=[str(x) for x in soup.find_all(string=True) if x.parent.name not in ('style','script') and str(x).strip()]
paths={
'folder':'M3 7h6l2-3h10v16H3z',
'compass':'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm4 5-3 5-5 3 3-5z',
'code':'m8 7-5 5 5 5m8-10 5 5-5 5m-3-14-2 18',
'data':'M4 4h16v16H4zM4 9h16M4 14h16M9 4v16',
'model':'M5 5h4v4H5zM15 15h4v4h-4zM15 5h4v4h-4zM7 9v8h8M9 7h6',
'play':'m8 4 12 8-12 8z',
'chart':'M4 3v17h17M8 16v-5m5 5V6m5 10V9',
'app':'M3 4h18v16H3zM3 9h18M7 6h1m3 0h1',
'check':'m5 12 4 4L19 6',
'tool':'m14 6 4 4m-8 4-6 6-2-2 6-6M14 3a5 5 0 0 0-6 7l6 6a5 5 0 0 0 7-6l-4 1-4-4z',
'book':'M12 5C9 3 5 3 3 4v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-2-1-6-1-9 1zm0 0v15',
'eye':'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zm10-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
'decide':'M12 3v8M5 20v-6h14v6M12 11v3M9 6l3-3 3 3',
'pen':'m4 16 12-12 4 4L8 20H4zm10-10 4 4',
'clock':'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm0 3v6l4 2'}
def icon(name):
    return BeautifulSoup(f'<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="{paths[name]}"/></svg>','html.parser').svg
mapping={'carpetas':'folder','preparacion':'compass','contexto':'code','datos':'data','modelos':'model','automatizacion':'play','reporte':'chart','app':'app','entrega':'check','problemas':'tool','fuentes':'book'}
for section in soup.select('main > section'):
    name=mapping[section['id']]
    section.h2.insert(0,icon(name))
    link=soup.select_one('nav a[href="#'+section['id']+'"]')
    if link: link.insert(0,icon(name))
for span in soup.select('.time'): span.insert(0,icon('clock'))
for el in soup.select('p'):
    strong=el.find('strong',recursive=False)
    if not strong: continue
    label=strong.get_text().lower()
    if label.startswith(('revisa','verifica','comprueba','criterio')):
        el['class']=el.get('class',[])+['review-note']; el.insert(0,icon('eye'))
    elif label.startswith(('decide','decisión')):
        el['class']=el.get('class',[])+['decision-note']; el.insert(0,icon('decide'))
for el in soup.select('.callout'):
    el.insert(0,icon('decide' if 'decision' in el.get('class',[]) else 'compass'))
for pre in soup.select('pre.prompt-manual'):
    detail=soup.new_tag('details',attrs={'class':'prompt-panel'})
    summary=soup.new_tag('summary'); summary.append(icon('pen')); summary.append('Prompt para escribir en Codex')
    detail.append(summary); pre.wrap(detail)
for h in soup.select('#datos h3, #modelos h3'):
    m=re.match(r'(\d+)\.\s*(.*)',h.get_text())
    if m:
        # Preserve the complete original heading text, with its number highlighted.
        text=h.get_text(); h.clear()
        badge=soup.new_tag('span',attrs={'class':'step-badge','aria-hidden':'true'}); badge.string=m[1]
        h.append(badge); label=soup.new_tag('span'); label.string=text; h.append(label)
route=soup.new_tag('div',attrs={'class':'visual-route','aria-label':'Ruta del taller'})
for target,label,desc in [('datos','Explora','Fuentes → EDA'),('modelos','Modela','Comparación → validación'),('automatizacion','Automatiza','Notebook → script'),('reporte','Comunica','EDA + explicabilidad'),('app','Utiliza','Modelo → inferencia')]:
    a=soup.new_tag('a',href='#'+target);a.append(icon(mapping[target]));b=soup.new_tag('strong');b.string=label;a.append(b);small=soup.new_tag('span');small.string=desc;a.append(small);route.append(a)
soup.select_one('header').append(route)
legend=BeautifulSoup('<div class="reading-key" aria-label="Claves de lectura"><span>Escribe · instrucción para Codex</span><span>Revisa · evidencia que comprobar</span><span>Decide · criterio que te corresponde</span></div>','html.parser').div
for el,name in zip(legend.select('span'),['pen','eye','decide']): el.insert(0,icon(name))
soup.select_one('#contexto h3').insert_before(legend)
css='''
/* Visual reading aids: local SVG icons, no external dependencies. */
.ui-icon{width:22px;height:22px;flex:none;vertical-align:middle;display:inline-block;margin-right:9px}
h2{display:flex;align-items:flex-start;gap:12px}h2>.ui-icon{width:34px;height:34px;color:var(--blue);margin:0}
nav a{display:flex;align-items:center;line-height:1.35}nav .ui-icon{width:18px;height:18px}
.visual-route{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;max-width:1100px;margin-top:30px}
.visual-route a{padding:17px;border:1px solid #506775;border-radius:12px;color:#eef7fa;text-decoration:none;background:#203d4d;display:grid;gap:8px}
.visual-route a:hover{background:#2c4f61;border-color:#f4ce75}.visual-route .ui-icon{color:#f4ce75;width:28px;height:28px}.visual-route strong{font-size:17px}.visual-route span{font-size:13px;color:#d5e7ee}
.reading-key{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}.reading-key>span{font-size:13px;padding:10px 12px;background:#edf3f5;border-radius:8px}
.review-note,.decision-note{padding:16px 18px;border-radius:8px;border:1px solid #ccdfda;background:#f0f7f4;font-size:16px}
.decision-note{background:#fff8e9;border-color:#e9d7ad}.review-note>.ui-icon{color:#20664d}.decision-note>.ui-icon{color:#805c13}
.callout>.ui-icon{float:left;margin-top:3px}.time .ui-icon{width:16px;height:16px}
.prompt-panel{padding:0;border-color:#becfd8;overflow:hidden;margin:18px 0}.prompt-panel>summary{padding:15px 18px;background:#edf3f6;color:#16475b;font-size:15px}.prompt-panel>summary:hover{background:#e1edf2}.prompt-panel[open]>summary{border-bottom:1px solid #becfd8}.prompt-panel pre{margin:0;border-radius:0;padding:22px}
#datos h3,#modelos h3{display:flex;align-items:flex-start;gap:12px;border-top:1px solid var(--line);padding-top:25px;margin-top:32px}.step-badge{display:flex;align-items:center;justify-content:center;flex:0 0 32px;height:32px;border-radius:50%;background:#125d78;color:white;font-size:15px}
#carpetas th:first-child{min-width:125px}td code{font-size:13px}tbody tr:nth-child(even){background:#f8fafb}
@media(max-width:1050px){.visual-route{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:600px){.visual-route{grid-template-columns:repeat(2,minmax(0,1fr))}.visual-route a{padding:13px}.visual-route a:last-child{grid-column:1/-1}h2{font-size:24px}h2>.ui-icon{width:26px;height:26px}.reading-key{display:grid}.review-note,.decision-note{padding:14px}section{padding:22px 16px}}
@media print{.visual-route{display:none}.prompt-panel>pre{display:block!important}.ui-icon{color:inherit}}
'''
soup.style.append(css)
result=str(soup)
# Verify every original prose/code string is retained, even within collapsed prompts.
visible=BeautifulSoup(result,'html.parser').get_text()
missing=[x for x in original if x not in visible]
assert not missing,missing[:5]
p.write_text(result,encoding='utf-8')
print('Contenido conservado; iconos, ruta visual, ayudas de revisión y 19 prompts desplegables añadidos.')
