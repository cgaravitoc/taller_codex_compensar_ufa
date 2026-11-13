"""Funciones compartidas del taller. Sin acceso a la referencia del facilitador."""
from pathlib import Path
from collections import defaultdict, deque
import json
import re
import numpy as np
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
NUMERIC = ['monto_cop','hora_dia','es_fin_semana','numero_cuotas','uso_3ds',
           'es_internacional','fuera_ciudad','dispositivo_nuevo','comercio_nuevo',
           'compras_previas_1h','monto_previo_24h','media_monto_previo',
           'ratio_monto_historico','minutos_desde_anterior','cupo_tarjeta_cop',
           'antiguedad_tarjeta_meses','score_crediticio','utilizacion_cupo_tarjetas']
CATEGORICAL = ['canal','categoria_comercio','metodo_autenticacion']
FEATURES = NUMERIC + CATEGORICAL

def load_inputs(data_dir=None):
    p = Path(data_dir or ROOT/'data')
    return (pd.read_excel(p/'clientes.xlsx',sheet_name='Clientes'),
            pd.read_csv(p/'centrales_riesgo.csv',sep=';'),
            pd.read_parquet(p/'transacciones.parquet'),
            pd.read_csv(p/'observacion_fraude.txt',sep='|',parse_dates=['fecha_cierre']))

def clean_transactions(raw, clients):
    """Reglas de dominio fijas; no estima medianas ni usa etiquetas."""
    required={'id_cliente','id_transaccion','id_tarjeta','fecha_hora','monto_cop','canal',
              'categoria_comercio','metodo_autenticacion','numero_cuotas','uso_3ds',
              'pais_compra','ciudad_compra','id_dispositivo','id_comercio'}
    missing=required-set(raw)
    if missing: raise ValueError(f'Faltan columnas: {sorted(missing)}')
    d=raw.copy()
    for key in ['id_cliente','id_transaccion','id_tarjeta']:
        if d[key].isna().any(): raise ValueError(f'Llave nula: {key}')
    if d.id_transaccion.duplicated().any(): raise ValueError('id_transaccion duplicado')
    if not clients.id_cliente.is_unique: raise ValueError('Clientes duplicados')
    references=clients[['id_cliente','id_tarjeta','cupo_tarjeta_cop']]
    joined=d[['id_cliente','id_tarjeta']].merge(references,on=['id_cliente','id_tarjeta'],how='left',validate='many_to_one')
    if joined.cupo_tarjeta_cop.isna().any(): raise ValueError('Cliente/tarjeta sin referencia')
    text=d.monto_cop.astype('string').str.strip()
    # Solo la forma COP 123.456,78 tiene una regla inequívoca de normalización.
    local=text.str.fullmatch(r'COP (?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}',na=False)
    text.loc[local]=text.loc[local].str.replace('COP ','',regex=False).str.replace('.','',regex=False).str.replace(',','.',regex=False)
    amount=pd.to_numeric(text,errors='coerce')
    invalid=amount.isna() | amount.le(0) | amount.gt(joined.cupo_tarjeta_cop.to_numpy())
    d['monto_cop']=amount.mask(invalid).astype(float)
    d['canal']=d.canal.astype('string').str.strip().str.upper()
    if not d.canal.isin(['POS','WEB','APP']).all(): raise ValueError('Canal desconocido')
    d['fecha_hora']=pd.to_datetime(d.fecha_hora,errors='coerce')
    if d.fecha_hora.isna().any(): raise ValueError('fecha_hora canónica inválida')
    d['fecha']=d.fecha_hora.dt.strftime('%Y-%m-%d')
    d['hora']=d.fecha_hora.dt.strftime('%H:%M:%S')
    # No se utilizan como predictores columnas >80% nulas, casi constantes o identificadores.
    quality={'filas_entrada':len(raw),'filas_salida':len(d),
             'montos_formato_local_recuperados':int(local.sum()),
             'montos_invalidos_a_nulo':int(invalid.sum()),
             'canales_normalizados':int((raw.canal!=d.canal).sum()),
             'fechas_reconstruidas':int((raw.fecha!=d.fecha).sum()) if 'fecha' in raw else len(d),
             'horas_reconstruidas':int((raw.hora!=d.hora).sum()) if 'hora' in raw else len(d)}
    return d.sort_values(['fecha_hora','id_transaccion']).reset_index(drop=True),quality

def historical_features(d):
    """Estado causal por cliente. La compra actual se añade DESPUÉS de calcular variables.

    Cada lote debe incluir historia previa o declarar inicio en frío. No usa etiquetas.
    Empates temporales se ordenan por id_transaccion, convención de este ejercicio.
    """
    d=d.sort_values(['fecha_hora','id_transaccion']).reset_index(drop=True).copy()
    state={}
    output=[]
    cols=['id_cliente','fecha_hora','monto_cop','canal','id_dispositivo','id_comercio']
    for customer,ts,amount,channel,device,merchant in d[cols].itertuples(index=False,name=None):
        if customer not in state:
            state[customer]={'hour':deque(),'day':deque(),'total':0.,'n':0,'last':None,'devices':set(),'shops':set()}
        s=state[customer]; now=ts.timestamp()
        while s['hour'] and s['hour'][0]<=now-3600: s['hour'].popleft()
        while s['day'] and s['day'][0][0]<=now-86400: s['day'].popleft()
        mean=s['total']/s['n'] if s['n'] else np.nan
        newdevice=float(device not in s['devices']) if channel!='POS' and pd.notna(device) else np.nan
        output.append([len(s['hour']),sum(x[1] for x in s['day']),mean,
                       amount/mean if pd.notna(amount) and pd.notna(mean) and mean>0 else np.nan,
                       (now-s['last'])/60 if s['last'] is not None else np.nan,
                       newdevice,float(merchant not in s['shops'])])
        s['hour'].append(now); s['last']=now; s['shops'].add(merchant)
        if pd.notna(device): s['devices'].add(device)
        if pd.notna(amount):
            s['day'].append((now,float(amount))); s['total']+=amount; s['n']+=1
    names=['compras_previas_1h','monto_previo_24h','media_monto_previo','ratio_monto_historico',
           'minutos_desde_anterior','dispositivo_nuevo','comercio_nuevo']
    d[names]=pd.DataFrame(output,index=d.index)
    d['hora_dia']=d.fecha_hora.dt.hour
    d['es_fin_semana']=(d.fecha_hora.dt.dayofweek>=5).astype(int)
    d['es_internacional']=(d.pais_compra!='CO').astype(int)
    return d

def build_features(raw, clients, bureau):
    d,quality=clean_transactions(raw,clients)
    d=historical_features(d)
    d=d.merge(clients,on=['id_cliente','id_tarjeta'],how='left',validate='many_to_one')
    d=d.merge(bureau,on='id_cliente',how='left',validate='many_to_one',suffixes=('_cliente','_buro'))
    if d.score_crediticio.isna().any(): raise ValueError('Falta registro de buró')
    for col in ['fecha_corte_cliente','fecha_corte_buro']:
        if not (pd.to_datetime(d[col])<d.fecha_hora).all(): raise ValueError('Referencia posterior a la compra')
    d['fuera_ciudad']=(d.ciudad_compra!=d.ciudad_residencia).astype(int)
    return d,quality

def prepare_dataset(data_dir=None,save=True):
    clients,bureau,raw,observed=load_inputs(data_dir)
    features,quality=build_features(raw,clients,bureau)
    if not observed.id_transaccion.is_unique: raise ValueError('Etiquetas duplicadas')
    base=features.merge(observed[['id_transaccion','es_fraude','fecha_cierre']],on='id_transaccion',how='left',validate='one_to_one')
    if base.es_fraude.isna().any(): raise ValueError('Etiquetas faltantes')
    if save:
        (ROOT/'artifacts').mkdir(exist_ok=True)
        base.to_parquet(ROOT/'artifacts/base_modelo.parquet',index=False)
        (ROOT/'artifacts/calidad.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
    return base,quality

def temporal_split(base):
    # Entrenamiento disponible 1 abril; validación abril madura antes del despliegue 16 junio.
    train=base[(base.fecha_hora<'2026-04-01') & (base.fecha_cierre<'2026-04-01')].copy()
    valid=base[(base.fecha_hora>='2026-04-01') & (base.fecha_hora<'2026-05-01') & (base.fecha_cierre<'2026-06-16')].copy()
    test=base[base.fecha_hora>='2026-06-16'].copy()
    assert train.fecha_hora.max()<valid.fecha_hora.min()<test.fecha_hora.min()
    assert train.fecha_cierre.max()<pd.Timestamp('2026-04-01')
    assert valid.fecha_cierre.max()<pd.Timestamp('2026-06-16')
    return train,valid,test

def make_pipeline(kind='logistica',**params):
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import OneHotEncoder,StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.dummy import DummyClassifier
    num=Pipeline([('imputar',SimpleImputer(strategy='median',add_indicator=True)),('escalar',StandardScaler())])
    cat=Pipeline([('imputar',SimpleImputer(strategy='most_frequent')),
                  ('codificar',OneHotEncoder(handle_unknown='ignore',sparse_output=False))])
    prep=ColumnTransformer([('numericas',num,NUMERIC),('categoricas',cat,CATEGORICAL)])
    if kind=='logistica': estimator=LogisticRegression(max_iter=500,random_state=SEED,**params)
    elif kind=='boosting': estimator=HistGradientBoostingClassifier(random_state=SEED,max_iter=100,early_stopping=False,**params)
    elif kind=='dummy': estimator=DummyClassifier(strategy='prior')
    else: raise ValueError(kind)
    return Pipeline([('preparar',prep),('modelo',estimator)])

def measure(y,p,threshold=.5):
    from sklearn.metrics import average_precision_score,roc_auc_score,precision_score,recall_score,f1_score,confusion_matrix,brier_score_loss
    predicted=p>=threshold
    return {'n':len(y),'prevalencia':float(np.mean(y)),'average_precision':float(average_precision_score(y,p)),
            'roc_auc':float(roc_auc_score(y,p)),'precision':float(precision_score(y,predicted,zero_division=0)),
            'recall':float(recall_score(y,predicted,zero_division=0)),'f1':float(f1_score(y,predicted,zero_division=0)),
            'brier':float(brier_score_loss(y,p)),'tasa_alertas':float(np.mean(predicted)),
            'matriz_confusion':confusion_matrix(y,predicted,labels=[0,1]).tolist()}

def predict_features(features, bundle):
    absent=set(FEATURES)-set(features)
    if absent: raise ValueError(f'Faltan predictores: {sorted(absent)}')
    p=bundle['pipeline'].predict_proba(features[FEATURES])[:,1]
    result=features[['id_transaccion','id_cliente','fecha_hora','monto_cop']].copy()
    result['riesgo_estimado']=p
    result['alerta']=(p>=bundle['threshold']).astype(int)
    result['version_modelo']=bundle['version']
    return result

def load_model(path=None):
    # Cargar únicamente artefactos propios: joblib utiliza pickle.
    return joblib.load(path or ROOT/'artifacts/modelo_fraude.joblib')

def rank_customers(predictions):
    # El máximo es un criterio de prioridad, no una probabilidad a nivel cliente.
    return predictions.groupby('id_cliente').agg(riesgo_maximo=('riesgo_estimado','max'),
        alertas=('alerta','sum'),transacciones=('id_transaccion','count'),
        monto_observado_cop=('monto_cop',lambda s:s.sum(min_count=1))).sort_values(['alertas','riesgo_maximo'],ascending=False).reset_index()
