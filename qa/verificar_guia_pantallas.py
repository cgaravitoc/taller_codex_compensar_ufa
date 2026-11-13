from pathlib import Path
import json
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(Path('guia/index.html').resolve().as_uri())
    assert page.locator('main > section:visible').count()==1
    ids=page.locator('main > section').evaluate_all('(els)=>els.map(e=>e.id)')
    for i,sid in enumerate(ids):
        page.locator('nav a[href="#'+sid+'"]').click()
        assert page.locator('main > section:visible').get_attribute('id')==sid
        assert page.locator('nav [aria-current="step"]').count()==1
        assert page.evaluate('document.activeElement.tagName')=='H2'
    page.locator('[data-screen-prev]').first.click()
    assert page.locator('#problemas').is_visible()
    page.go_back(); assert page.locator('#fuentes').is_visible()
    page.goto(Path('guia/index.html').resolve().as_uri()+'#datos')
    summaries=page.locator('#datos > .lesson-step > summary')
    summaries.nth(1).focus();page.keyboard.press('Enter')
    assert page.locator('#datos > .lesson-step[open]').count()==1
    assert summaries.nth(1).evaluate('el=>el.parentElement.open')
    panel=page.locator('#datos > .lesson-step[open] .prompt-panel > summary').first
    panel.focus();page.keyboard.press('Enter')
    prompt=page.locator('#datos > .lesson-step[open] .prompt-manual').first
    assert prompt.is_visible()
    assert prompt.evaluate("el=>!el.dispatchEvent(new Event('copy',{bubbles:true,cancelable:true}))")
    page.locator('#datos [data-step]').check()
    page.reload();assert page.locator('#datos').is_visible();assert page.locator('#datos [data-step]').is_checked()
    page.screenshot(path='qa/browser/guia_pantallas_desktop.png')
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#screen-select').select_option('modelos')
    assert page.locator('#modelos').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path='qa/browser/guia_pantallas_mobile.png')
    for sid in ids:
        page.locator('#screen-select').select_option(sid)
        assert page.locator('main > section:visible').count()==1
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),sid
    # Keyboard skip link reaches the currently visible screen heading.
    page.keyboard.press('Control+Home');page.locator('.skip-link').focus();page.keyboard.press('Enter')
    assert page.evaluate('document.activeElement.tagName')=='H2'
    assert not errors,errors
    # Text/controls use measured opaque palette pairs.
    def lum(h):
        vals=[int(h[i:i+2],16)/255 for i in (0,2,4)]
        vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals]
        return sum(v*w for v,w in zip(vals,[.2126,.7152,.0722]))
    ratios={a+'/'+b:round((max(lum(a),lum(b))+.05)/(min(lum(a),lum(b))+.05),2) for a,b in [('ffffff','125d78'),('465e6d','f4f7f8'),('123f50','dcebf0'),('142c3b','ffffff')]}
    assert all(v>=4.5 for v in ratios.values()),ratios
    result={'screens':len(ids),'keyboard':'passed','history':'passed','progress':'passed','mobile':'passed','copy_block':'passed','console_errors':errors,'contrast_ratios':ratios,'limits':'Sin prueba con lector de pantalla; contraste medido en paleta principal.'}
    Path('qa/guia_pantallas_validacion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(result)
    browser.close()
