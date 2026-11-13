import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from taller import clean_transactions,historical_features,load_inputs,load_model,predict_features,FEATURES,temporal_split

@pytest.fixture(scope='module')
def inputs(): return load_inputs()

def test_cleaning_preserves_keys_and_handles_invalid_amounts(inputs):
    c,b,t,o=inputs
    clean,q=clean_transactions(t,c)
    assert set(clean.id_transaccion)==set(t.id_transaccion)
    assert q['montos_invalidos_a_nulo']==4000
    assert q['montos_formato_local_recuperados']==2000
    assert clean.monto_cop.dropna().gt(0).all()

def test_reject_duplicate_and_unknown_customer(inputs):
    c,b,t,o=inputs
    with pytest.raises(ValueError,match='duplicado'):
        clean_transactions(pd.concat([t.head(2),t.head(1)],ignore_index=True),c)
    bad=t.head(1).copy(); bad['id_cliente']='CLI99999'
    with pytest.raises(ValueError,match='sin referencia'): clean_transactions(bad,c)

def test_history_is_causal(inputs):
    c,b,t,o=inputs
    customer=t.id_cliente.iloc[0]
    clean,_=clean_transactions(t[t.id_cliente==customer],c)
    expected=historical_features(clean)
    future=clean.iloc[-1:].copy()
    future['id_transaccion']='FUTURO'; future['fecha_hora']=clean.fecha_hora.max()+pd.Timedelta(days=10); future['monto_cop']=999999.
    actual=historical_features(pd.concat([clean,future],ignore_index=True)).iloc[:-1]
    cols=['media_monto_previo','compras_previas_1h','monto_previo_24h','dispositivo_nuevo']
    pd.testing.assert_frame_equal(expected[cols],actual[cols])
    assert np.isnan(expected.iloc[0].media_monto_previo)
    assert expected.iloc[0].compras_previas_1h==0

def test_pipeline_and_temporal_labels():
    base=pd.read_parquet(ROOT/'artifacts/base_modelo.parquet')
    train,valid,test=temporal_split(base)
    assert train.fecha_cierre.max()<pd.Timestamp('2026-04-01')
    assert valid.fecha_cierre.max()<test.fecha_hora.min()
    assert not set(FEATURES)&{'es_fraude','fecha_cierre','estado_caso','id_cliente','perdida_confirmada_cop'}
    bundle=load_model(); small=test.head(20).copy()
    small['categoria_comercio']='Categoria_no_vista'
    predictions=predict_features(small,bundle)
    assert predictions.riesgo_estimado.between(0,1).all()

def test_api_valid_and_invalid():
    from fastapi.testclient import TestClient
    sys.path.insert(0,str(ROOT))
    from app.api import app
    client=TestClient(app)
    event=dict(id_transaccion='PRUEBA_API',id_cliente='CLI00001',fecha_hora='2026-07-01T12:00:00',
        monto_cop=50000,canal='WEB',categoria_comercio='Tecnologia',id_comercio='COM_PRUEBA',
        ciudad_compra='Bogota',metodo_autenticacion='OTP',id_dispositivo='DEV_PRUEBA')
    response=client.post('/predict',json=event)
    assert response.status_code==200,response.text
    assert 0<=response.json()['riesgo_estimado']<=1
    assert client.post('/predict',json={**event,'monto_cop':-1}).status_code==422
    assert client.post('/predict',json={**event,'id_cliente':'CLI99999'}).status_code==422

def test_streamlit_form():
    from streamlit.testing.v1 import AppTest
    at=AppTest.from_file(str(ROOT/'app/streamlit_app.py'),default_timeout=60).run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception
    assert len(at.metric)==2
    assert at.metric[0].label=='Riesgo estimado'

def test_batch_matches_notebook():
    saved=pd.read_parquet(ROOT/'artifacts/predicciones_prueba.parquet')
    batch=pd.read_csv(ROOT/'reports/inferencia/predicciones.csv')
    joined=saved.merge(batch,on='id_transaccion',validate='one_to_one',suffixes=('_notebook','_script'))
    assert len(joined)==len(saved)==len(batch)
    assert np.allclose(joined.riesgo_estimado_notebook,joined.riesgo_estimado_script)
