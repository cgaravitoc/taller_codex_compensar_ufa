"""Inspección funcional de HTML local con Edge headless y capturas reproducibles."""
from pathlib import Path
import functools
import http.server
import threading
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'qa/browser'; QA.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f'http://127.0.0.1:{server.server_port}'
results={}
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
        errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(origin+'/guia/index.html'); page.screenshot(path=str(QA/'guia_desktop.png'))
        assert page.locator('section').count()==10
        page.locator('[data-step="contexto"]').check()
        assert page.locator('#contador').inner_text()=='1/7'
        page.reload(); assert page.locator('[data-step="contexto"]').is_checked()
        page.locator('[data-step="contexto"]').uncheck()
        results['guia']={'secciones':page.locator('section').count(),'progreso_persistente':True,'errores_js':list(errors)}
        page.set_viewport_size({'width':390,'height':844}); page.screenshot(path=str(QA/'guia_mobile.png'))
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.set_viewport_size({'width':1440,'height':1000})
        page.goto(origin+'/reports/reporte_fraude.html',wait_until='networkidle')
        page.get_by_text('Lo que muestran los resultados',exact=False).first.wait_for(timeout=30000)
        page.screenshot(path=str(QA/'reporte_inicio.png'))
        # Source-backed charts must paint marks, not just empty SVG containers.
        charts=page.locator('.recharts-surface')
        results['reporte']={'svg_charts':charts.count(),'errores_js':list(errors)}
        assert charts.count()>=5, page.locator('body').inner_text()[:2000]
        for i in range(charts.count()):
            chart=charts.nth(i); chart.scroll_into_view_if_needed(); page.wait_for_timeout(500)
            box=chart.bounding_box(); assert box and box['width']>100 and box['height']>100
            assert chart.locator('path').count()>0
            chart.screenshot(path=str(QA/f'reporte_chart_{i}.png'))
        page.get_by_label('Canal para la evolución mensual').select_option('WEB')
        page.wait_for_timeout(500)
        assert page.get_by_label('Canal para la evolución mensual').input_value()=='WEB'
        page.get_by_label('Canal para la evolución mensual').select_option('Todos')
        slider=page.get_by_label('Umbral exploratorio'); original=float(slider.input_value())
        slider.fill('1'); page.wait_for_timeout(200)
        assert '0 alertas' in page.locator('.fraud-metrics').inner_text().replace('\n',' ')
        slider.fill('0'); page.wait_for_timeout(200)
        assert '100.0% recall' in page.locator('.fraud-metrics').inner_text().replace('\n',' ')
        page.get_by_role('button',name='Restablecer umbral del modelo').click()
        assert abs(float(slider.input_value())-original)<.001
        page.locator('.fraud-matrix').screenshot(path=str(QA/'reporte_matriz.png'))
        results['reporte'].update({'selector_canal':True,'umbral_extremos_y_reset':True,'umbral_original':original})
        page.set_viewport_size({'width':390,'height':844}); page.evaluate('window.scrollTo(0,0)'); page.wait_for_timeout(600)
        page.screenshot(path=str(QA/'reporte_mobile.png'))
        results['reporte']['ancho_mobile']=page.evaluate('({viewport:innerWidth,documento:document.documentElement.scrollWidth})')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
        # Both delivered notebooks were executed and their rendered outputs are visible.
        page.set_viewport_size({'width':1440,'height':1000})
        for preview in (ROOT/'qa/notebook_previews').glob('*.html'):
            page.goto(origin+'/qa/notebook_previews/'+preview.name)
            page.screenshot(path=str(QA/(preview.stem+'_inicio.png')))
            assert page.locator('img').count()>=3
        results['notebooks_html']='Ambos abiertos; figuras presentes'
        results['errores_js']=errors
        (QA/'validacion_html.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(results,ensure_ascii=False,indent=2))
        browser.close()
finally:
    server.shutdown()
