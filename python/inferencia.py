"""Inferencia por lotes con el mismo contrato usado en entrenamiento.

Ejemplo: python python/inferencia.py --desde 2026-06-16
El archivo de entrada contiene también la historia anterior para calcular variables.
"""
import argparse
import logging
from pathlib import Path
import pandas as pd
from taller import ROOT,build_features,load_model,predict_features,rank_customers

def run(input_path,output_dir,desde=None,history_path=None):
    raw=pd.read_parquet(input_path)
    requested=set(raw.id_transaccion)
    if history_path:
        history=pd.read_parquet(history_path)
        if set(history.id_transaccion)&requested:
            raise ValueError('Historia y entrada se solapan; se requieren IDs distintos')
        raw=pd.concat([history,raw],ignore_index=True)
    clients=pd.read_excel(ROOT/'data/clientes.xlsx')
    bureau=pd.read_csv(ROOT/'data/centrales_riesgo.csv',sep=';')
    features,quality=build_features(raw,clients,bureau)
    selected=features.id_transaccion.isin(requested)
    if desde: selected &= features.fecha_hora>=pd.Timestamp(desde)
    features=features.loc[selected]
    if features.empty: raise ValueError('No hay compras para el periodo solicitado')
    bundle=load_model()
    output=predict_features(features,bundle)
    directory=Path(output_dir); directory.mkdir(parents=True,exist_ok=True)
    # Sobrescritura atómica y nombres estables: una ejecución no duplica alertas.
    for name,df in [('predicciones.csv',output),('prioridad_clientes.csv',rank_customers(output))]:
        path=directory/name; temp=path.with_suffix('.tmp')
        df.to_csv(temp,index=False,encoding='utf-8'); temp.replace(path)
    logging.info('Filas=%d, alertas=%d, limpieza=%s',len(output),output.alerta.sum(),quality)
    return output

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'data/transacciones.parquet')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'reports/inferencia')
    parser.add_argument('--desde',default='2026-06-16')
    parser.add_argument('--historia',type=Path,help='Parquet de historia anterior, sin IDs solapados')
    args=parser.parse_args()
    (ROOT/'logs').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',
        handlers=[logging.FileHandler(ROOT/'logs/inferencia.log',encoding='utf-8'),logging.StreamHandler()])
    try: run(args.input,args.output_dir,args.desde,args.historia)
    except Exception:
        logging.exception('Fallo de inferencia'); raise

if __name__=='__main__': main()
