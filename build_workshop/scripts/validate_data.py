"""Read back final artifacts and validate the workshop data contract."""
from pathlib import Path
import sys
import json
import hashlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.python_deps'))
import pandas as pd
import numpy as np

c = pd.read_excel(ROOT/'data/clientes.xlsx',sheet_name='Clientes')
b = pd.read_csv(ROOT/'data/centrales_riesgo.csv',sep=';')
raw = pd.read_parquet(ROOT/'data/transacciones.parquet')
# Original business invariants are evaluated on the facilitator reference.
# Separate raw checks below must prove that only the declared defects were introduced.
t = pd.read_parquet(ROOT/'qa/facilitador/transacciones_original.parquet')
o = pd.read_csv(ROOT/'data/observacion_fraude.txt',sep='|',parse_dates=['fecha_reporte','fecha_cierre','fecha_corte_observacion'])
checks = {}
def check(name, condition):
    checks[name] = bool(condition)
    assert condition, name

check('crudo_200000_filas_23_columnas',raw.shape==(200000,23))
unchanged=[col for col in t if col not in ['monto_cop','fecha','hora','canal']]
pd.testing.assert_frame_equal(raw[unchanged],t[unchanged])
check('llaves_e_instante_y_campos_no_intervenidos_intactos',True)
amount=pd.to_numeric(raw.monto_cop,errors='coerce')
date=pd.to_datetime(raw.fecha,format='%Y-%m-%d',errors='coerce')
time=pd.to_datetime(raw.hora,format='%H:%M:%S',errors='coerce')
quality_counts={
    'montos_no_numericos':int(amount.isna().sum()),
    'montos_extremos_mayores_100_millones':int(amount.gt(100000000).sum()),
    'montos_negativos':int(amount.lt(0).sum()),
    'montos_cero':int(amount.eq(0).sum()),
    'fechas_no_iso_validas':int(date.isna().sum()),
    'horas_invalidas':int(time.isna().sum()),
    'canales_fuera_catalogo':int((~raw.canal.isin(['POS','WEB','APP'])).sum()),
    'latencia_nulos':int(raw.latencia_red_ms.isna().sum()),
    'sdk_nulos':int(raw.version_sdk.isna().sum()),
    'sistema_origen_mayoritario':int(raw.sistema_origen.eq('CORE_TARJETAS').sum()),
    'reintento_valor_mayoritario':int(raw.indicador_reintento.eq(0).sum()),
}
expected_counts=dict(montos_no_numericos=4000,montos_extremos_mayores_100_millones=1000,
    montos_negativos=500,montos_cero=500,fechas_no_iso_validas=3000,horas_invalidas=1000,
    canales_fuera_catalogo=2000,latencia_nulos=170000,sdk_nulos=190000,
    sistema_origen_mayoritario=199000,reintento_valor_mayoritario=199800)
for key,expected in expected_counts.items():
    check('defecto_esperado_'+key,quality_counts[key]==expected)
check('canales_recuperables',raw.canal.str.strip().str.upper().equals(t.canal))
# Verify unchanged cells and the instructor ledger, not only aggregate quotas.
ledger=pd.read_csv(ROOT/'qa/facilitador/defectos_inyectados.csv',keep_default_na=False,dtype=str)
check('bitacora_12000_celdas_sin_duplicados',len(ledger)==12000 and not ledger.duplicated(['id_transaccion','columna']).any())
positions=pd.Series(raw.index,index=raw.id_transaccion)
for col in ['monto_cop','fecha','hora','canal']:
    edits=ledger[ledger.columna==col]
    indexes=positions.loc[edits.id_transaccion].to_numpy()
    check('bitacora_valores_'+col,np.array_equal(raw.loc[indexes,col].astype(str).to_numpy(),edits.valor_inyectado.to_numpy()))
    check('bitacora_original_'+col,np.array_equal(t.loc[indexes,col].astype(str).to_numpy(),edits.valor_original.to_numpy()))
    rest=raw.index.difference(indexes)
    left=pd.to_numeric(raw.loc[rest,col]) if col=='monto_cop' else raw.loc[rest,col]
    check('celdas_no_intervenidas_'+col,np.array_equal(left.to_numpy(),t.loc[rest,col].to_numpy()))
quality_report={
    'estado':'DEFECTOS_INTENCIONALES_VERIFICADOS_NO_APTO_PARA_MODELAR_SIN_LIMPIEZA',
    'filas':len(raw),'columnas':raw.shape[1], 'semilla_calidad':20261114,
    'conteos':quality_counts,'porcentajes':{k:round(v/len(raw)*100,3) for k,v in quality_counts.items()},
    'celdas_modificadas_en_columnas_existentes':len(ledger),
    'filas_con_modificaciones_en_columnas_existentes':int(ledger.id_transaccion.nunique()),
    'referencia_facilitador':'qa/facilitador/transacciones_original.parquet',
    'nota':'Los controles de negocio originales se ejecutan sobre la referencia limpia. El crudo contiene los defectos listados.'}
(ROOT/'qa/calidad_transacciones.json').write_text(json.dumps(quality_report,ensure_ascii=False,indent=2),encoding='utf-8')

check('5000_clientes',len(c)==5000 and c.id_cliente.is_unique)
check('buro_25_variables',len(b)==5000 and b.shape[1]==27 and b.id_cliente.is_unique)
check('200000_transacciones',len(t)==200000 and t.id_transaccion.is_unique)
check('seguimiento_completo',len(o)==200000 and o.id_transaccion.is_unique and set(o.id_transaccion)==set(t.id_transaccion))
check('tasa_fraude_exacta',o.es_fraude.sum()==50000 and o.es_fraude.mean()==.25)
check('llaves_clientes',set(t.id_cliente)==set(c.id_cliente)==set(b.id_cliente))
merged=t.merge(c,on=['id_cliente','id_tarjeta'],validate='many_to_one')
check('tarjeta_corresponde_cliente',len(merged)==200000 and c.id_tarjeta.is_unique)
check('perfil_previo', (pd.to_datetime(merged.fecha_corte)<merged.fecha_hora).all())
check('buro_previo',pd.to_datetime(b.fecha_corte).max()<t.fecha_hora.min())
check('periodo_compras',t.fecha_hora.min()>=pd.Timestamp('2026-01-01') and t.fecha_hora.max()<pd.Timestamp('2026-07-01'))
check('fechas_horas_consistentes',(t.fecha==t.fecha_hora.dt.strftime('%Y-%m-%d')).all() and (t.hora==t.fecha_hora.dt.strftime('%H:%M:%S')).all())
check('montos_y_cupos', (merged.monto_cop>0).all() and (merged.monto_cop<=merged.cupo_tarjeta_cop).all())
check('compras_internacionales_habilitadas',merged.loc[merged.pais_compra!='CO','compras_internacionales_habilitadas'].eq(1).all())
check('categorias_comercios_estables',t.groupby('id_comercio').categoria_comercio.nunique().max()==1)
check('dispositivo_solo_digital',t.loc[t.canal=='POS','id_dispositivo'].isna().all() and t.loc[t.canal!='POS','id_dispositivo'].notna().all())
check('autenticacion_3ds',((t.metodo_autenticacion=='3DS')==(t.uso_3ds==1)).all())
check('buro_saldos', (b.saldo_total_deuda_cop>=b.saldo_rotativo_cop).all() and (b.saldo_en_mora_cop<=b.saldo_total_deuda_cop).all())
check('buro_utilizacion', np.allclose(b.saldo_rotativo_cop/b.cupo_total_tarjetas_cop,b.utilizacion_cupo_tarjetas,atol=1e-7))
check('buro_moras_anidadas',(b.obligaciones_mora_30d>=b.obligaciones_mora_60d).all() and (b.obligaciones_mora_60d>=b.obligaciones_mora_90d).all())
check('buro_consultas_anidadas',(b.consultas_buro_6m>=b.consultas_buro_3m).all() and (b.consultas_buro_3m>=b.consultas_buro_1m).all())
check('buro_obligaciones', (b.numero_tarjetas_credito+b.numero_creditos_consumo==b.numero_obligaciones_activas).all())
check('ultima_mora_coherente',b.loc[b.eventos_mora_12m==0,'meses_desde_ultima_mora'].dropna().gt(12).all() and b.loc[b.eventos_mora_12m>0,'meses_desde_ultima_mora'].le(12).all())
check('cuatro_insumos',set(p.name for p in (ROOT/'data').iterdir())=={'clientes.xlsx','centrales_riesgo.csv','transacciones.parquet','observacion_fraude.txt'})
z=t.merge(o,on='id_transaccion',validate='one_to_one')
check('cierres_maduros', ((z.fecha_cierre>z.fecha_hora)&(z.fecha_cierre<=z.fecha_corte_observacion)).all())
inv=z.fue_investigada==1
check('reportes_ordenados',(z.loc[inv,'fecha_reporte']>z.loc[inv,'fecha_hora']).all() and (z.loc[inv,'fecha_cierre']>z.loc[inv,'fecha_reporte']).all() and z.loc[~inv,'fecha_reporte'].isna().all())
check('ventana_45_dias',((z.loc[~inv,'fecha_cierre']-z.loc[~inv,'fecha_hora']).dt.days==45).all())
check('etiquetas_estados',((z.estado_caso=='FRAUDE_CONFIRMADO')==(z.es_fraude==1)).all())
check('perdidas_validas',((z.perdida_confirmada_cop>=0)&(z.perdida_confirmada_cop<=z.monto_cop)).all() and z.loc[z.es_fraude==0,'perdida_confirmada_cop'].eq(0).all())
check('sin_objetivo_en_predictores','es_fraude' not in t and 'es_fraude' not in c and 'es_fraude' not in b)
check('faltantes_didacticos',c.ingreso_mensual_cop.isna().sum()==150)
for name,df in [('clientes',c),('centrales_riesgo',b),('transacciones',raw),('observacion_fraude',o)]:
    schema=json.loads((ROOT/f'data_dict/{name}.json').read_text(encoding='utf-8'))
    check(f'diccionario_completo_{name}',list(df.columns)==[s['campo'] for s in schema])
    check(f'diccionario_cuatro_atributos_{name}',all(set(s)=={'campo','tipo','descripcion','dominio'} for s in schema))

report = {
    'resultado':'OK_CONTRATO_DIDACTICO_CON_DEFECTOS_INTENCIONALES', 'semilla':20261113, 'controles':checks,
    'calidad_cruda':quality_report,
    'filas':{'clientes':len(c),'centrales_riesgo':len(b),'transacciones':len(t),'observacion_fraude':len(o)},
    'fraudes':int(o.es_fraude.sum()),'tasa_fraude':float(o.es_fraude.mean()),
    'estados':o.estado_caso.value_counts().to_dict(),
    'tasas_por_canal':z.groupby('canal').es_fraude.mean().to_dict(),
    'tasas_por_mes':z.groupby(z.fecha_hora.dt.strftime('%Y-%m')).es_fraude.mean().to_dict(),
    'archivos':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((ROOT/'data').iterdir()) if p.is_file()}
}
(ROOT/'qa/validacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
