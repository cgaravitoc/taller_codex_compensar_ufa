r"""API opcional: .venv\Scripts\python -m uvicorn app.api:app --host 127.0.0.1 --port 8000"""
import sys
from pathlib import Path
from typing import Literal
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field,ConfigDict
from servicio import score_transaction

app=FastAPI(title='Fraude sintético · API del taller',version='1.0')
class Transaction(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id_transaccion:str=Field(min_length=1,max_length=50)
    id_cliente:str=Field(pattern=r'^CLI\d{5}$')
    fecha_hora:datetime
    monto_cop:float=Field(gt=0,le=60000000,allow_inf_nan=False)
    canal:Literal['POS','WEB','APP']
    categoria_comercio:Literal['Supermercado','Restaurante','Tecnologia','Viajes','Moda','Servicios']
    id_comercio:str=Field(min_length=1,max_length=50)
    pais_compra:Literal['CO','US','MX','ES']='CO'
    ciudad_compra:str=Field(min_length=1,max_length=80)
    numero_cuotas:Literal[1,3,6,12,24]=1
    metodo_autenticacion:Literal['CHIP_PIN','CONTACTLESS','3DS','OTP']
    id_dispositivo:str|None=None

@app.get('/health')
def health(): return {'status':'ok','modelo_disponible':(Path(__file__).resolve().parents[1]/'artifacts/modelo_fraude.joblib').exists()}

@app.post('/predict')
def predict(payload:Transaction):
    try: return score_transaction(payload.model_dump())
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e)) from e
    except FileNotFoundError as e: raise HTTPException(status_code=503,detail='Ejecute el notebook 02 para generar el modelo') from e
