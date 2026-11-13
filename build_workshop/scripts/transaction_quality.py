"""Inject reproducible ingestion defects AFTER fraud labels have been generated.

No target or customer attributes are used to choose affected rows.
The pristine reference and instructor evidence live outside participant data/.
"""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.python_deps'))
import numpy as np
import pandas as pd

QUALITY_SEED = 20261114

def inject_quality(clean, root=ROOT):
    if len(clean) != 200000:
        raise ValueError('This quality exercise requires exactly 200000 transactions.')
    if 'sistema_origen' in clean:
        raise ValueError('Input is already contaminated; use the pristine reference.')
    rng = np.random.default_rng(QUALITY_SEED)
    dirty = clean.copy(deep=True)
    ledger = []

    def change(indices, column, values, issue):
        values = list(values)
        for idx, new in zip(indices, values, strict=True):
            ledger.append({'id_transaccion':str(clean.at[idx,'id_transaccion']),
                           'columna':column,'defecto':issue,
                           'valor_original':str(clean.at[idx,column]),'valor_inyectado':str(new)})
        dirty.loc[indices,column] = values

    # Parquet is typed: malformed numeric inputs require a physical string column.
    dirty['monto_cop'] = clean.monto_cop.map(lambda x:f'{x:.2f}').astype('string')
    rows = rng.permutation(len(clean))[:6000]
    change(rows[:2000], 'monto_cop',
           ['COP '+f'{v:,.2f}'.replace(',','X').replace('.',',').replace('X','.') for v in clean.loc[rows[:2000],'monto_cop']],
           'monto_formato_moneda_local')
    change(rows[2000:3000], 'monto_cop', ['no_disponible']*1000, 'monto_texto_no_numerico')
    change(rows[3000:4000], 'monto_cop', ['1O0O']*1000, 'monto_letra_O_por_cero')
    change(rows[4000:5000], 'monto_cop',
           [f'{v*100+100000000:.2f}' for v in clean.loc[rows[4000:5000],'monto_cop']], 'monto_extremo_error_escala')
    change(rows[5000:5500], 'monto_cop',
           [f'{-v:.2f}' for v in clean.loc[rows[5000:5500],'monto_cop']], 'monto_negativo')
    change(rows[5500:6000], 'monto_cop', ['0.00']*500, 'monto_cero')
    rows = rng.permutation(len(clean))[:3000]
    change(rows[:1500], 'fecha', pd.to_datetime(clean.loc[rows[:1500],'fecha']).dt.strftime('%d/%m/%Y'), 'fecha_formato_dia_mes')
    change(rows[1500:], 'fecha', ['2026-02-30']*1500, 'fecha_imposible')
    rows = rng.choice(len(clean),1000,replace=False)
    change(rows, 'hora', ['25:61:99']*1000, 'hora_imposible')
    rows = rng.choice(len(clean),2000,replace=False)
    change(rows, 'canal', [' '+v.lower()+' ' for v in clean.loc[rows,'canal']], 'canal_espacios_minusculas')

    dirty['latencia_red_ms'] = rng.lognormal(np.log(120),.4,len(clean)).round(2)
    dirty.loc[rng.choice(len(clean),170000,replace=False),'latencia_red_ms'] = np.nan
    dirty['version_sdk'] = pd.Series(rng.choice(['2.1.0','2.2.0','2.3.0'],len(clean)),dtype='string')
    dirty.loc[rng.choice(len(clean),190000,replace=False),'version_sdk'] = pd.NA
    dirty['sistema_origen'] = 'CORE_TARJETAS'
    dirty.loc[rng.choice(len(clean),1000,replace=False),'sistema_origen'] = 'PASARELA_LEGACY'
    dirty['indicador_reintento'] = np.zeros(len(clean),dtype=np.int8)
    dirty.loc[rng.choice(len(clean),200,replace=False),'indicador_reintento'] = 1

    qa = root/'qa/facilitador'
    qa.mkdir(parents=True,exist_ok=True)
    clean.to_parquet(qa/'transacciones_original.parquet',index=False,compression='snappy')
    pd.DataFrame(ledger).to_csv(qa/'defectos_inyectados.csv',index=False,encoding='utf-8')
    return dirty

NEW_FIELDS = {
    'latencia_red_ms': ('float64','Latencia de red observada al autorizar. Falta por perdida simulada de telemetria, no por no aplicabilidad.','Milisegundos >0; 85% nulos exactos','predictor'),
    'version_sdk': ('string','Version del SDK de captura de telemetria. Ausencia de captura simulada.','2.1.0; 2.2.0; 2.3.0; 95% nulos exactos','predictor'),
    'sistema_origen': ('string','Sistema que envia el registro. Variable categorica casi constante.','CORE_TARJETAS 99.5%; PASARELA_LEGACY 0.5%','baja_variabilidad'),
    'indicador_reintento': ('int8','Indica si hubo un reintento tecnico antes de completar la compra.','0=99.9%; 1=0.1%','baja_variabilidad'),
}
NOTES = {
    'monto_cop': ' Captura cruda almacenada como texto: 4000 formatos no canonicos, 1000 errores de escala, 500 negativos y 500 ceros. Requiere normalizacion y validacion.',
    'fecha': ' Contiene 1500 fechas DD/MM/AAAA y 1500 fechas imposibles. fecha_hora conserva el instante canonico para contraste.',
    'hora': ' Contiene 1000 horas imposibles. fecha_hora conserva el instante canonico para contraste.',
    'canal': ' Contiene 2000 registros con espacios y minusculas; normalizar antes de evaluar el dominio.',
}

def update_dictionary(dirty, root=ROOT):
    path = root/'data_dict/transacciones.json'
    fields = json.loads(path.read_text(encoding='utf-8'))
    by_name = {f['campo']:f for f in fields}
    for col, (_, description, domain, role) in NEW_FIELDS.items():
        by_name[col] = dict(campo=col,descripcion=description,dominio=domain)
    result=[]
    for col in dirty:
        field=by_name[col]
        note=NOTES.get(col,'')
        if note and note not in field['descripcion']:
            field['descripcion'] += note
        field['tipo']=str(dirty[col].dtype)
        result.append({key:field[key] for key in ['campo','tipo','descripcion','dominio']})
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Diccionario: transacciones','',
           '| Campo | Tipo | Descripcion | Dominio / unidad |',
           '|---|---|---|---|']
    for f in result:
        lines.append('| '+' | '.join(str(f[k]) for k in ['campo','tipo','descripcion','dominio'])+' |')
    (root/'data_dict/transacciones.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':
    # Rerunning always starts from the clean backup; defects never accumulate.
    backup=ROOT/'qa/facilitador/transacciones_original.parquet'
    source=backup if backup.exists() else ROOT/'data/transacciones.parquet'
    pristine=pd.read_parquet(source)
    dirty=inject_quality(pristine)
    dirty.to_parquet(ROOT/'data/transacciones.parquet',index=False,compression='snappy')
    update_dictionary(dirty)
    print('Transacciones actualizadas: 200000 filas, 23 columnas. Llaves y etiquetas preservadas.')
