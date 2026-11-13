from pathlib import Path
from bs4 import BeautifulSoup
p=Path('guia/index.html');soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
original=[str(x) for x in soup.find_all(string=True) if x.parent.name not in ('style','script') and str(x).strip()]
main=soup.main;main['id']='contenido'
# Group long sections without dropping or rewriting their contents.
for sid in ['carpetas','datos','modelos']:
    section=soup.find(id=sid)
    for idx,h in enumerate(list(section.find_all('h3',recursive=False))):
        group=[]
        for sibling in list(h.next_siblings):
            if getattr(sibling,'name',None)=='h3': break
            if getattr(sibling,'name',None)=='label' and 'check' in sibling.get('class',[]): break
            group.append(sibling)
        detail=soup.new_tag('details',attrs={'class':'lesson-step','name':'steps-'+sid})
        if idx==0: detail['open']=''
        summary=soup.new_tag('summary');h.wrap(detail);summary.append(h.extract());detail.insert(0,summary)
        for node in group: detail.append(node.extract())
# Native select keeps mobile navigation compact and keyboard accessible.
nav=soup.select_one('nav[aria-label="Contenido del taller"]')
options=''.join('<option value="'+a['href'][1:]+'">'+a.get_text(strip=True)+'</option>' for a in nav.select('a[href^="#"]'))
mobile=BeautifulSoup('<div class="screen-picker"><label for="screen-select">Ir a una etapa</label><select id="screen-select">'+options+'</select></div>','html.parser').div
nav.insert(0,mobile)
controls='''<div class="screen-controls" aria-label="Navegación entre etapas"><button type="button" data-screen-prev>← Anterior</button><span class="screen-position" aria-live="polite"></span><button type="button" data-screen-next>Siguiente →</button></div>'''
main.insert(0,BeautifulSoup(controls,'html.parser').div)
main.append(BeautifulSoup(controls,'html.parser').div)
skip=BeautifulSoup('<a class="skip-link" href="#contenido">Saltar al contenido de la etapa</a>','html.parser').a
soup.body.insert(0,skip)
soup.style.append('''
/* Screen-based workshop navigation; ordinary document remains available without JS. */
[hidden]{display:none!important}
.screen-controls,.screen-picker,.skip-link{display:none}
.paged header{padding:22px max(4vw,24px)}.paged header h1{font-size:28px;line-height:1.15;margin:8px 0}.paged header h1 br{display:none}.paged header h1 br:after{content:' '}.paged header .lead{font-size:16px;max-width:1000px;margin:8px 0}.paged header>p:last-of-type{font-size:13px;margin:4px 0}.paged .visual-route{display:none}
.paged .layout{padding-top:22px;gap:28px}.paged main>section{margin-bottom:20px;min-height:360px}
.paged .screen-controls{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 18px;padding:12px 0}.screen-controls button{font:600 14px system-ui;padding:12px 18px;min-height:44px;border-radius:8px;border:1px solid #125d78;background:#125d78;color:white;cursor:pointer}.screen-controls button:disabled{background:#e5ebee;color:#52626b;border-color:#b9c5cb;cursor:default}.screen-position{font-size:14px;color:#465e6d;text-align:center}
.paged nav a[aria-current="step"]{background:#dcebf0;border-left-color:#125d78;font-weight:700;color:#123f50}.paged nav a{min-height:44px}
.paged .skip-link:focus{display:block;position:fixed;top:8px;left:8px;z-index:100;background:white;padding:14px;border:3px solid #125d78}.paged .skip-link{display:block;position:absolute;left:-10000px}
.lesson-step{padding:0;overflow:hidden;margin:18px 0;border:1px solid #c5d6df}.lesson-step>summary{padding:16px 18px;background:#eef4f6;list-style:disclosure-closed}.lesson-step[open]>summary{list-style:disclosure-open;border-bottom:1px solid #c5d6df}.lesson-step>summary h3,#datos .lesson-step>summary h3,#modelos .lesson-step>summary h3{display:inline;font-size:18px;border:0;padding:0;margin:0}.lesson-step .step-badge{display:none}.lesson-step>summary h3>span:last-child{display:inline}.lesson-step> :not(summary){margin-left:18px;margin-right:18px}.lesson-step> :last-child{margin-bottom:18px}
main h2:focus{outline:3px solid #d08412;outline-offset:6px}
@media(max-width:850px){.paged header{padding:18px 20px}.paged header h1{font-size:23px}.paged header .lead{font-size:14px}.paged .layout{gap:8px;padding:16px}.paged nav{display:block}.paged nav>a,.paged nav>strong{display:none}.paged .screen-picker{display:block}.screen-picker label{display:block;font-size:13px;font-weight:700;margin-bottom:5px}.screen-picker select{font:16px system-ui;width:100%;padding:12px;background:white;color:#142c3b;border:1px solid #9fb5c0;border-radius:8px;min-height:46px}.paged .progress{margin:10px 0}.paged .progress p{display:none}.paged .screen-controls{gap:6px}.screen-controls button{padding:10px;font-size:13px}.screen-position{font-size:12px}.lesson-step>summary{padding:14px}.lesson-step>summary h3,#datos .lesson-step>summary h3,#modelos .lesson-step>summary h3{font-size:16px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{.paged main>section[hidden]{display:block!important}.screen-controls,.screen-picker,.skip-link{display:none!important}.lesson-step::details-content,.prompt-panel::details-content{content-visibility:visible!important}.lesson-step>*,.prompt-panel>*{display:block!important}.paged header{padding:12px}.paged main>section{min-height:0}}
''')
script='''
// Each stage has its own URL fragment and restores on reload.
const screens=[...document.querySelectorAll('main > section')];
const screenLinks=[...document.querySelectorAll('nav a[href^="#"]')];
const picker=document.getElementById('screen-select');
let screenIndex=0;
function showScreen(id,focus=false){
  const found=screens.findIndex(section=>section.id===id);
  screenIndex=found<0?0:found;
  screens.forEach((section,index)=>section.hidden=index!==screenIndex);
  const current=screens[screenIndex];
  screenLinks.forEach(link=>{
    if(link.hash==='#'+current.id) link.setAttribute('aria-current','step');
    else link.removeAttribute('aria-current');
  });
  picker.value=current.id;
  document.querySelectorAll('.screen-position').forEach(el=>el.textContent=`Pantalla ${screenIndex+1} de ${screens.length}`);
  document.querySelectorAll('[data-screen-prev]').forEach(b=>b.disabled=screenIndex===0);
  document.querySelectorAll('[data-screen-next]').forEach(b=>b.disabled=screenIndex===screens.length-1);
  document.title=current.querySelector('h2').textContent.trim()+' · Taller Codex';
  try{localStorage.setItem('codex-taller-screen',current.id)}catch(e){}
  if(focus){
    const heading=current.querySelector('h2');heading.tabIndex=-1;heading.focus({preventScroll:true});
    document.querySelector('main').scrollIntoView({behavior:'instant',block:'start'});
  }
}
function goScreen(id){
  if(location.hash==='#'+id) showScreen(id,true);
  else location.hash=id;
}
document.querySelectorAll('[data-screen-prev]').forEach(b=>b.addEventListener('click',()=>goScreen(screens[screenIndex-1].id)));
document.querySelectorAll('[data-screen-next]').forEach(b=>b.addEventListener('click',()=>goScreen(screens[screenIndex+1].id)));
picker.addEventListener('change',()=>goScreen(picker.value));
window.addEventListener('hashchange',()=>{
  const id=location.hash.slice(1);
  if(screens.some(section=>section.id===id)) showScreen(id,true);
});
document.querySelector('.skip-link').addEventListener('click',event=>{event.preventDefault();showScreen(screens[screenIndex].id,true)});
let storedScreen='';try{storedScreen=localStorage.getItem('codex-taller-screen')||''}catch(e){}
document.body.classList.add('paged');
showScreen(location.hash.slice(1)||storedScreen);
// Opening a lesson starts at its heading, keeping the task in view.
document.querySelectorAll('.lesson-step').forEach(detail=>detail.addEventListener('toggle',()=>{
  if(detail.open && !detail.closest('section').hidden && document.activeElement===detail.querySelector('summary')){
    detail.scrollIntoView({behavior:'instant',block:'start'});
  }
}));
let printOpen=[];
window.addEventListener('beforeprint',()=>{printOpen=[...document.querySelectorAll('details')].filter(d=>!d.open);printOpen.forEach(d=>{d.dataset.printName=d.getAttribute('name')||'';d.removeAttribute('name');d.open=true})});
window.addEventListener('afterprint',()=>{printOpen.forEach(d=>{d.open=false;if(d.dataset.printName)d.setAttribute('name',d.dataset.printName);delete d.dataset.printName})});
'''
soup.script.append(script)
result=str(soup).replace('viewbox=', 'viewBox=')
text=BeautifulSoup(result,'html.parser').get_text()
assert all(x in text for x in original),'Se detectó pérdida de contenido'
p.write_text(result,encoding='utf-8')
print('11 pantallas, navegación por hash, pasos desplegables y contenido íntegro.')
