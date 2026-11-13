"""Entrenamiento reproducible. Los notebooks llaman a estas mismas funciones."""
import json
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from taller import ROOT,FEATURES,NUMERIC,CATEGORICAL,SEED,make_pipeline,measure,temporal_split,prepare_dataset

def compare_models(train,valid):
    fitted={}; rows=[]
    for name,kind in [('Dummy','dummy'),('Logistica','logistica'),('Boosting_base','boosting')]:
        start=time.perf_counter(); model=make_pipeline(kind)
        model.fit(train[FEATURES],train.es_fraude)
        metrics=measure(valid.es_fraude,model.predict_proba(valid[FEATURES])[:,1])
        rows.append({'modelo':name,**{k:v for k,v in metrics.items() if k!='matriz_confusion'},'segundos':time.perf_counter()-start})
        fitted[name]=model
    return fitted,pd.DataFrame(rows)

def optimize(train,valid,fitted,comparison):
    rows=comparison.to_dict('records')
    for name,params in [('Boosting_15',{'max_leaf_nodes':15,'l2_regularization':1.}),
                        ('Boosting_31',{'max_leaf_nodes':31,'l2_regularization':3.})]:
        start=time.perf_counter(); model=make_pipeline('boosting',**params)
        model.fit(train[FEATURES],train.es_fraude)
        metrics=measure(valid.es_fraude,model.predict_proba(valid[FEATURES])[:,1])
        rows.append({'modelo':name,**{k:v for k,v in metrics.items() if k!='matriz_confusion'},'segundos':time.perf_counter()-start})
        fitted[name]=model
    comparison=pd.DataFrame(rows).sort_values('average_precision',ascending=False)
    winner=comparison.iloc[0].modelo
    model=fitted[winner]
    scores=model.predict_proba(valid[FEATURES])[:,1]
    # Presupuesto didáctico: alertar aproximadamente el 20% en validación.
    threshold=float(np.quantile(scores,.80))
    return model,winner,threshold,comparison

def evaluate_and_save(model,winner,threshold,comparison,train,valid,test):
    p=model.predict_proba(test[FEATURES])[:,1]
    test_metrics=measure(test.es_fraude,p,threshold)
    valid_metrics=measure(valid.es_fraude,model.predict_proba(valid[FEATURES])[:,1],threshold)
    sample=valid.sample(min(2000,len(valid)),random_state=SEED)
    importance=permutation_importance(model,sample[FEATURES],sample.es_fraude,
        scoring='average_precision',n_repeats=3,random_state=SEED,n_jobs=1)
    importances=pd.DataFrame({'variable':FEATURES,'importancia_media':importance.importances_mean,
                              'desviacion':importance.importances_std}).sort_values('importancia_media',ascending=False)
    artifacts=ROOT/'artifacts'; artifacts.mkdir(exist_ok=True)
    bundle={'pipeline':model,'threshold':threshold,'features':FEATURES,'version':'fraude-sintetico-v1',
            'winner':winner,'trained_as_of':'2026-04-01','deployed_as_of':'2026-06-16',
            'reference_numeric':train[NUMERIC].median().to_dict(),
            'reference_categorical':{c:train[c].mode().iloc[0] for c in CATEGORICAL}}
    joblib.dump(bundle,artifacts/'modelo_fraude.joblib')
    comparison.to_csv(artifacts/'comparacion_modelos.csv',index=False)
    importances.to_csv(artifacts/'importancia_permutacion.csv',index=False)
    result={'modelo':winner,'umbral':threshold,'validacion':valid_metrics,'prueba':test_metrics,
            'particiones':{name:{'filas':len(d),'desde':str(d.fecha_hora.min()),'hasta':str(d.fecha_hora.max()),
                                 'ultima_etiqueta':str(d.fecha_cierre.max()),'prevalencia':float(d.es_fraude.mean())}
                          for name,d in [('entrenamiento',train),('validacion',valid),('prueba',test)]},
            'importancia_muestra':len(sample),'importancia_repeticiones':3}
    (artifacts/'metricas.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    scored=test[['id_transaccion','id_cliente','fecha_hora','monto_cop','canal','categoria_comercio','es_fraude']].copy()
    scored['riesgo_estimado']=p; scored['alerta']=(p>=threshold).astype(int)
    scored.to_parquet(artifacts/'predicciones_prueba.parquet',index=False)
    return result,importances,scored

def main():
    base,_=prepare_dataset(); train,valid,test=temporal_split(base)
    fitted,table=compare_models(train,valid)
    model,winner,threshold,table=optimize(train,valid,fitted,table)
    result,_,_=evaluate_and_save(model,winner,threshold,table,train,valid,test)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
