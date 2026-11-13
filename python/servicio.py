"""Inferencia individual reutilizada por Streamlit y FastAPI."""
from functools import lru_cache
import pandas as pd
from taller import ROOT,FEATURES,NUMERIC,CATEGORICAL,load_model,build_features,predict_features

@lru_cache(maxsize=1)
def context():
    return (load_model(),pd.read_excel(ROOT/'data/clientes.xlsx'),
            pd.read_csv(ROOT/'data/centrales_riesgo.csv',sep=';'),
            pd.read_parquet(ROOT/'data/transacciones.parquet'))

def score_transaction(event):
    bundle,clients,bureau,history=context()
    event=dict(event); customer=event['id_cliente']
    profile=clients[clients.id_cliente==customer]
    if profile.empty: raise ValueError('Cliente no encontrado en clientes.xlsx')
    ts=pd.Timestamp(event['fecha_hora'])
    if ts.tzinfo is not None: raise ValueError('Use hora local America/Bogota sin sufijo de zona')
    amount=float(event['monto_cop'])
    if not 0<amount<=float(profile.iloc[0].cupo_tarjeta_cop): raise ValueError('Monto fuera del cupo o no positivo')
    if ts<pd.Timestamp(bundle['deployed_as_of']): raise ValueError('La demostracion usa el modelo disponible desde 2026-06-16')
    event['id_tarjeta']=profile.iloc[0].id_tarjeta
    if history.id_transaccion.eq(event['id_transaccion']).any(): raise ValueError('El ID ya existe; use un ID nuevo')
    prior=history[(history.id_cliente==customer) & (history.fecha_hora<ts)].copy()
    event['fecha_hora']=ts; event['fecha']=ts.strftime('%Y-%m-%d'); event['hora']=ts.strftime('%H:%M:%S')
    event['id_dispositivo']=event.get('id_dispositivo') if event['canal']!='POS' else None
    event['uso_3ds']=int(event['metodo_autenticacion']=='3DS')
    event['moneda_liquidacion']='COP'; event['resultado_autenticacion']='EXITOSA'
    if event['canal']=='POS' and event['metodo_autenticacion'] not in ['CHIP_PIN','CONTACTLESS']:
        raise ValueError('Autenticacion no compatible con POS')
    if event['canal']!='POS' and event['metodo_autenticacion'] not in ['3DS','OTP']:
        raise ValueError('Autenticacion digital debe ser 3DS u OTP')
    if event['pais_compra']!='CO' and not profile.iloc[0].compras_internacionales_habilitadas:
        raise ValueError('Cliente sin compras internacionales habilitadas')
    batch=pd.concat([prior,pd.DataFrame([event])],ignore_index=True)
    features,_=build_features(batch,clients,bureau)
    row=features[features.id_transaccion==event['id_transaccion']]
    result=predict_features(row,bundle).iloc[0]
    return {'id_transaccion':event['id_transaccion'],'id_cliente':customer,
            'riesgo_estimado':float(result.riesgo_estimado),'alerta':bool(result.alerta),
            'umbral':bundle['threshold'],'version_modelo':bundle['version'],
            'compras_previas_consultadas':len(prior),
            'contexto':{'hora_dia':int(row.iloc[0].hora_dia),'compras_previas_1h':int(row.iloc[0].compras_previas_1h),
                        'comercio_nuevo':bool(row.iloc[0].comercio_nuevo)},
            'nota':'Demostracion sin persistencia: dos llamadas no acumulan historia. Score no calibrado para prevalencia real.'}
