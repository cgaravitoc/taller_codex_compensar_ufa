"""Construye evidencia del reporte y exporta el HTML interactivo autocontenido.

Requiere Node y el plugin Data de Codex para recompilar la fuente React.
El HTML ya entregado se abre sin instalaciones ni conexión.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from taller import ROOT,rank_customers

def build_snapshot():
    source=ROOT/'reports/fuente/src/data.json'
    snapshot=json.loads(source.read_text(encoding='utf-8'))
    base=pd.read_parquet(ROOT/'artifacts/base_modelo.parquet')
    raw=pd.read_parquet(ROOT/'data/transacciones.parquet')
    predictions=pd.read_parquet(ROOT/'artifacts/predicciones_prueba.parquet')
    metrics=json.loads((ROOT/'artifacts/metricas.json').read_text(encoding='utf-8'))
    quality=json.loads((ROOT/'artifacts/calidad.json').read_text(encoding='utf-8'))
    comparison=pd.read_csv(ROOT/'artifacts/comparacion_modelos.csv')
    importance=pd.read_csv(ROOT/'artifacts/importancia_permutacion.csv')
    labels={'ratio_monto_historico':'Monto relativo','dispositivo_nuevo':'Disp. nuevo',
            'metodo_autenticacion':'Autenticación','hora_dia':'Hora','minutos_desde_anterior':'Min. sin compra',
            'fuera_ciudad':'Otra ciudad','es_internacional':'Internacional','media_monto_previo':'Media previa',
            'monto_cop':'Monto','numero_cuotas':'Cuotas'}
    importance['etiqueta']=importance.variable.map(labels).fillna(importance.variable)
    queries={}
    def query(name,df,description,files,method):
        rows=json.loads(df.to_json(orient='records',date_format='iso'))
        queries[name]={'rows':rows,'source':{'type':'file','name':description,
            'files':files,'description':description,'classification':'synthetic',
            'evidenceFlow':[{'title':'Datos sintéticos','detail':'Cuatro insumos en data/. Etiquetas maduras al 15 de agosto de 2026.'},
                            {'title':'Transformación','detail':method}],
            'metricDefinitions':[{'label':description,'definition':method}]},
            'methods':[{'language':'python','code':method}]}
    query('summary',pd.DataFrame([{'clientes':base.id_cliente.nunique(),'compras':len(base),'fraudes':int(base.es_fraude.sum()),
        'fraudRate':float(base.es_fraude.mean()),'modelo':metrics['modelo'],'umbral':metrics['umbral'],
        **{k:v for k,v in metrics['prueba'].items() if k!='matriz_confusion'}}]),
        'Resumen de población y prueba temporal',['data/','artifacts/metricas.json'],
        'Población: clientes únicos, conteo y suma de es_fraude. Métricas: python/entrenar.py::evaluate_and_save; prueba del 16 al 30 de junio.')
    query('nulls',pd.DataFrame({'campo':raw.columns,'nullRate':raw.isna().mean().values}).sort_values('nullRate',ascending=False),
        'Nulos antes de limpiar',['data/transacciones.parquet'],'raw.isna().mean(); denominador: 200000 compras. Los textos inválidos no cuentan como nulos físicos.')
    query('quality',pd.DataFrame([{'regla':k,'cantidad':v} for k,v in quality.items()]),'Decisiones de limpieza',
        ['artifacts/calidad.json'],'python/taller.py::clean_transactions; reglas de formato, cupo y timestamp canónico, sin eliminar compras.')
    group=base.assign(mes=base.fecha_hora.dt.strftime('%Y-%m-01')).groupby(['mes','canal']).es_fraude.agg(['size','sum']).reset_index()
    group['fraudRate']=group['sum']/group['size']; group=group.rename(columns={'size':'compras','sum':'fraudes'})
    query('monthly',group,'Fraude mensual por canal',['artifacts/base_modelo.parquet'],
        'Agrupar por mes y canal: compras=size, fraudes=sum(es_fraude), fraudRate=fraudes/compras. Enero-junio; descriptivo global.')
    hours=base.groupby(base.fecha_hora.dt.hour).es_fraude.agg(['size','mean']).reset_index().rename(columns={'fecha_hora':'hora','size':'compras','mean':'fraudRate'})
    query('hours',hours,'Fraude por hora local',['artifacts/base_modelo.parquet'],'Agrupar por hora America/Bogota; mean(es_fraude). Descriptivo, no causal.')
    query('comparison',comparison,'Comparación en validación',['artifacts/comparacion_modelos.csv'],
        'Modelos ajustados en entrenamiento; Average Precision en abril selecciona ganador. Métricas de esta tabla a umbral 0.5.')
    query('importance',importance,'Importancia global por permutación',['artifacts/importancia_permutacion.csv'],
        '2000 compras de validación, 3 repeticiones; caída de Average Precision al permutar una variable. Desviación entre repeticiones, no intervalo de confianza.')
    query('test',predictions,'Predicciones de prueba',['artifacts/predicciones_prueba.parquet'],
        'Compras de 16 a 30 junio. Score del modelo congelado; objetivo posterior solo para evaluación. Un cambio interactivo de umbral es exploratorio, no reoptimización válida.')
    ranking=rank_customers(predictions)
    query('ranking',ranking,'Prioridad de clientes',['artifacts/predicciones_prueba.parquet'],
        'Agrupar por cliente; ordenar alertas descendentes y riesgo máximo descendente. Monto suma solo valores válidos; máximo score no es probabilidad del cliente.')
    snapshot.update(title='Fraude sintético: de la calidad a las alertas',surface='report',buildStatus='complete',
        status='complete',report={'asOf':'2026-08-15'},queries=queries,
        exportPreferences={'selected':None,'destinations':[]})
    source.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
    return metrics

def export_html():
    configured=os.environ.get('DATA_PLUGIN_ROOT')
    candidates=list((Path.home()/'.codex/plugins/cache/openai-curated-remote/data-analytics').glob('*/scripts/data-app.mjs'))
    tool=Path(configured)/'scripts/data-app.mjs' if configured else (sorted(candidates)[-1] if candidates else None)
    if tool is None or not tool.exists():
        raise RuntimeError('Para regenerar el HTML instale el plugin Data de Codex o defina DATA_PLUGIN_ROOT. El HTML entregado funciona sin ese plugin.')
    node=shutil.which('node')
    if not node: raise RuntimeError('Node no está disponible en PATH')
    project=ROOT/'reports/fuente'
    subprocess.run([node,str(tool),'build','--project-dir',str(project),'--separate-data'],check=True)
    exported=project/'.data-app-offline/exports/reporte_fraude.html'
    subprocess.run([node,str(tool),'export-offline','--project-dir',str(project),'--output',str(exported)],check=True)
    shutil.copy2(exported,ROOT/'reports/reporte_fraude.html')
    print('Reporte listo:',ROOT/'reports/reporte_fraude.html')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--solo-datos',action='store_true')
    args=parser.parse_args(); build_snapshot()
    if not args.solo_datos: export_html()
