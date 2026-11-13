"""Revisión visual de Streamlit; inicia y detiene únicamente su propio proceso."""
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
qa=ROOT/'qa/browser'; qa.mkdir(parents=True,exist_ok=True)
log=(qa/'streamlit_server.log').open('w',encoding='utf-8')
proc=subprocess.Popen([sys.executable,'-m','streamlit','run',str(ROOT/'app/streamlit_app.py'),
    '--server.address','127.0.0.1','--server.port','18501','--server.headless','true','--browser.gatherUsageStats','false'],
    cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
try:
    for _ in range(100):
        try:
            urllib.request.urlopen('http://127.0.0.1:18501/_stcore/health',timeout=1); break
        except Exception: time.sleep(.2)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100})
        page.goto('http://127.0.0.1:18501')
        page.get_by_role('button',name='Evaluar transacción').wait_for(timeout=60000)
        page.get_by_role('button',name='Evaluar transacción').click()
        page.get_by_text('Resultado de la última evaluación',exact=True).wait_for()
        page.get_by_text('Riesgo estimado',exact=True).wait_for(timeout=60000)
        page.get_by_role('button',name='Descargar resultado JSON').wait_for(timeout=30000)
        assert page.get_by_text('Creator of Delta protobuf messages.',exact=False).count()==0
        page.get_by_text('Variables relevantes para el modelo',exact=True).scroll_into_view_if_needed()
        page.wait_for_timeout(2000)
        page.screenshot(path=str(qa/'streamlit_explicabilidad.png'))
        page.get_by_role('heading',name='Radar de fraude',exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(qa/'streamlit_desktop.png'),full_page=True)
        assert page.get_by_test_id('stMetric').count()==2
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(qa/'streamlit_mobile.png'),full_page=True)
        result={'formulario_en_navegador':True,'inferencia_renderizada':True,'metricas':2,
                'ancho_mobile':page.evaluate('({viewport:innerWidth,documento:document.documentElement.scrollWidth})')}
        (qa/'streamlit_validacion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False))
        browser.close()
finally:
    if proc.poll() is None:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    log.close()
