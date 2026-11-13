"""Construye los dos cuadernos tutoriales. No ejecuta modelos."""
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]
def md(text): return nbf.v4.new_markdown_cell(text)
def code(text): return nbf.v4.new_code_cell(text)
setup="""from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd() / 'data').exists() else Path.cwd().parent
assert (ROOT / 'data/transacciones.parquet').exists(), 'Abra el repositorio y seleccione .venv'
sys.path.insert(0, str(ROOT / 'python'))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({'figure.figsize': (10, 4), 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
from taller import *
print('Repositorio:', ROOT.name)
"""
nb1=[md('''# 01 · Integrar, limpiar y explorar los datos

**Objetivo:** construir una base transaccional verificable sin perder compras ni utilizar el resultado de la investigación como predictor.

**Tiempo de práctica: 20 minutos.** Datos enteramente sintéticos: 5.000 clientes, 200.000 compras y 25% de fraude por diseño. Este cuaderno es una solución ejecutable; modifica una comprobación y explica tu decisión para producir evidencia individual.

## Preparación
Seleccione el kernel `.venv`. Ejecute las celdas en orden. Los diccionarios están en `data/data_dict/`. No use la referencia limpia de `build_workshop/qa/facilitador/` para resolver el ejercicio.'''),code(setup),
md('''## 1. Leer cuatro formatos
El Excel describe clientes; el CSV con `;` contiene 25 variables de buró; Parquet contiene compras; el TXT con `|` contiene seguimiento y etiquetas. Una fila representa una compra en la tabla central.'''),
code("""clientes, buro, transacciones, observacion = load_inputs()
display(pd.DataFrame({'fuente':['clientes','buro','transacciones','observacion'],
                      'filas':[len(clientes),len(buro),len(transacciones),len(observacion)],
                      'columnas':[clientes.shape[1],buro.shape[1],transacciones.shape[1],observacion.shape[1]]}))
display(transacciones.head(3))"""),
md('''## 2. Validar las llaves antes de unir
Un cliente tiene muchas compras. Cada compra tiene una sola observación. `validate=` evita que una unión muchos-a-muchos multiplique silenciosamente las filas.'''),
code("""assert clientes.id_cliente.is_unique and buro.id_cliente.is_unique
assert transacciones.id_transaccion.is_unique and observacion.id_transaccion.is_unique
assert not transacciones[['id_cliente','id_transaccion','id_tarjeta']].isna().any().any()
assert set(transacciones.id_cliente) == set(clientes.id_cliente) == set(buro.id_cliente)
assert set(transacciones.id_transaccion) == set(observacion.id_transaccion)
unida = transacciones[['id_transaccion','id_cliente']].merge(
    clientes[['id_cliente','edad']], on='id_cliente', validate='many_to_one').merge(
    observacion[['id_transaccion','es_fraude']], on='id_transaccion', validate='one_to_one')
assert len(unida) == 200_000
print('Unión:', len(unida), 'filas. Fraudes:', int(unida.es_fraude.sum()))"""),
md('''## 3. Perfilar calidad y variabilidad
Los nulos estructurales de dispositivo en POS tienen un significado distinto de la pérdida de telemetría. Una variable casi constante puede ser válida, aunque aporte poco al modelo.'''),
code("""perfil = pd.DataFrame({'tipo':transacciones.dtypes.astype(str),
    'nulos_pct':transacciones.isna().mean()*100,
    'distintos':transacciones.nunique(dropna=True),
    'moda_pct':transacciones.apply(lambda s: s.value_counts(normalize=True).iloc[0]*100 if s.notna().any() else np.nan)})
display(perfil.sort_values('nulos_pct',ascending=False).round(2))
perfil.nlargest(6,'nulos_pct').nulos_pct.sort_values().plot.barh(color='#20647c')
plt.xlabel('% de filas nulas'); plt.title('Ausencia de datos en 200.000 compras'); plt.xlim(0,100); plt.tight_layout(); plt.show()"""),
md('''## 4. Aplicar reglas explícitas de limpieza
Normalizamos moneda local y canal. Montos no recuperables, no positivos o superiores al cupo pasan a nulo; no eliminamos sus filas. La mediana se aprenderá exclusivamente con entrenamiento en el siguiente notebook. Reconstruimos fecha y hora desde el timestamp canónico. Consulte `python/taller.py::clean_transactions` para revisar el código.

**Decisión:** no corregir `1O0O` suponiendo que significa mil. Tampoco asumir que toda compra grande es fraude.'''),
code("""limpias, calidad = clean_transactions(transacciones, clientes)
display(pd.Series(calidad, name='resultado').to_frame())
assert len(limpias)==len(transacciones)
assert limpias.monto_cop.isna().sum()==4000
assert limpias.canal.isin(['POS','WEB','APP']).all()
assert (limpias.fecha==limpias.fecha_hora.dt.strftime('%Y-%m-%d')).all()
display(limpias[['monto_cop','canal','fecha','hora']].head())"""),
md('''## 5. Construir historia sin mirar el futuro
Para cada cliente ordenamos por timestamp y calculamos compras de la hora anterior, suma de montos de las últimas 24 horas, promedio previo, novedad de comercio/dispositivo y tiempo desde la compra anterior. La compra actual se añade al historial después del cálculo. Los primeros registros no tienen media previa.

El historial de compras puede usarse aunque todavía no se conozca su etiqueta. El historial de fraude requeriría controlar cuándo se confirmó cada caso.'''),
code("""base, calidad = prepare_dataset()
assert len(base)==200_000 and base.es_fraude.sum()==50_000
primera = base.sort_values(['fecha_hora','id_transaccion']).groupby('id_cliente').head(1)
assert primera.media_monto_previo.isna().all()
assert primera.compras_previas_1h.eq(0).all()
display(base[['id_cliente','fecha_hora','monto_cop','media_monto_previo','compras_previas_1h','dispositivo_nuevo']].head(8))"""),
md('''## 6. Explorar comportamientos
Este EDA global describe el conjunto sintético completo; no se utiliza para ajustar hiperparámetros ni seleccionar el umbral. En una evaluación ciega estricta, reserve también el EDA de prueba. Las asociaciones observadas no demuestran causalidad ni autoría del fraude.'''),
code("""por_canal = base.groupby('canal').agg(compras=('es_fraude','size'),fraudes=('es_fraude','sum'),tasa=('es_fraude','mean'))
display(por_canal)
fig, axes = plt.subplots(1,2,figsize=(12,4))
por_canal.tasa.mul(100).plot.bar(ax=axes[0],color='#20647c',rot=0)
axes[0].set(ylabel='% de compras con fraude',title='Fraude por canal',ylim=(0,100))
base.groupby(base.fecha_hora.dt.hour).es_fraude.mean().mul(100).plot(ax=axes[1],marker='o',color='#b55b23')
axes[1].set(xlabel='Hora local',ylabel='% de compras con fraude',title='Fraude por hora',xticks=range(0,24,3))
plt.tight_layout(); plt.show()"""),
code("""validos = base.monto_cop.dropna()
plt.hist(np.log10(validos),bins=40,color='#20647c',edgecolor='white')
plt.title(f'Monto después de limpiar · {len(validos):,} compras con monto válido')
plt.xlabel('log10(monto en COP)'); plt.ylabel('Número de compras'); plt.tight_layout(); plt.show()
print('Los nulos no aparecen en este histograma:', int(base.monto_cop.isna().sum()))"""),
md('''## Comprobaciones y entrega
Se guardaron `artifacts/base_modelo.parquet` y `artifacts/calidad.json`. Se conservaron todas las compras, y cada variable histórica utiliza únicamente datos previos.

**Evidencia individual:** capture el perfil de calidad, una comprobación de llaves y un gráfico. Escriba por qué un monto inválido se convirtió a nulo y por qué no se imputó antes de separar entrenamiento.

**Prompt para Codex:** «Revisa `clean_transactions` y `historical_features`. Identifica si una compra actual o futura puede alterar el historial previo. Propón una prueba que detecte ese error y ejecútala sin utilizar las etiquetas».

Continúe con `02_modelos_validacion.ipynb`.''')]
nb2=[md('''# 02 · Comparar, optimizar y validar modelos de ML

**Objetivo:** elegir un modelo y un umbral usando validación, evaluar una prueba temporal reservada y guardar el mismo pipeline que usarán los scripts y la app.

**Tiempo de práctica: 25 minutos.** Se comparan una referencia trivial, regresión logística y boosting. La optimización está acotada a dos configuraciones adicionales para caber en el taller; no equivale a una búsqueda exhaustiva.

## Preparación
Ejecute primero el notebook 01. Seleccione el kernel `.venv`.'''),code(setup),
code("""from entrenar import compare_models, optimize, evaluate_and_save
base = pd.read_parquet(ROOT/'artifacts/base_modelo.parquet')
train, valid, test = temporal_split(base)
display(pd.DataFrame([{'particion':n,'filas':len(d),'desde':d.fecha_hora.min(),'hasta':d.fecha_hora.max(),
                      'ultima_etiqueta':d.fecha_cierre.max(),'tasa_fraude':d.es_fraude.mean()}
                     for n,d in [('entrenamiento',train),('validacion',valid),('prueba',test)]]))"""),
md('''## 1. Respetar el tiempo y la maduración
- Entrenamiento: compras anteriores al 1 de abril cuya investigación/ventana ya había cerrado antes de esa fecha.
- Validación: compras de abril, con etiquetas maduras antes del 16 de junio.
- Prueba: compras del 16 al 30 de junio, evaluadas retrospectivamente con etiquetas consolidadas el 15 de agosto.

Las compras no incluidas en estas particiones siguen siendo historia disponible para las variables de comportamiento. La selección por maduración cambia la prevalencia del entrenamiento; compare las tasas mostradas. No usamos IDs, género, pérdida confirmada, estado de investigación ni fecha de cierre como predictores.

Esta evaluación mide nuevas compras de la cartera conocida. No demuestra generalización a clientes nuevos.'''),
code("""prohibidas={'es_fraude','fecha_cierre','perdida_confirmada_cop','estado_caso','id_cliente','id_transaccion','genero'}
assert not set(FEATURES)&prohibidas
assert train.fecha_cierre.max()<pd.Timestamp('2026-04-01')
assert valid.fecha_cierre.max()<pd.Timestamp('2026-06-16')
print('Predictores:', FEATURES)
display(make_pipeline('logistica'))"""),
md('''## 2. Comparar con una referencia
El pipeline aprende imputación, escalado y categorías solamente con entrenamiento. Average Precision resume la curva precisión–recall mediante saltos de recall; no es la integral trapezoidal de esa curva. El modelo trivial ayuda a interpretar la mejora sobre la prevalencia.

También medimos ROC-AUC, precisión, recall y Brier. Las métricas de clasificación iniciales usan 0,5; el umbral operativo se definirá después.'''),
code("""fitted, comparacion = compare_models(train, valid)
display(comparacion[['modelo','average_precision','roc_auc','precision','recall','segundos']].round(4))"""),
md('''## 3. Optimizar sin tocar prueba
Dos configuraciones de boosting modifican hojas y regularización. Elegimos la mayor Average Precision en la misma validación; este uso repetido puede sobreajustar validación, por eso prueba permanece reservada.

El presupuesto de alertas es un supuesto didáctico: aproximadamente 20% en validación. El umbral resultante no garantiza el mismo volumen en otros periodos.'''),
code("""modelo, ganador, umbral, comparacion = optimize(train, valid, fitted, comparacion)
display(comparacion[['modelo','average_precision','roc_auc','segundos']].round(4))
print('Ganador por validación:', ganador, '| Umbral:', round(umbral,4))
comparacion.sort_values('average_precision').plot.barh(x='modelo',y='average_precision',legend=False,color='#20647c')
plt.xlabel('Average Precision en validación'); plt.xlim(0,1); plt.title('Comparación de modelos · abril de 2026'); plt.tight_layout(); plt.show()"""),
md('''## 4. Evaluar prueba una sola vez
Congelamos modelo, predictores y umbral. La matriz permite distinguir falsos positivos —revisiones innecesarias— y falsos negativos —fraudes no alertados—. No cambiamos el modelo a partir de este resultado.'''),
code("""metricas, importancias, predicciones = evaluate_and_save(modelo, ganador, umbral, comparacion, train, valid, test)
display(pd.Series({k:v for k,v in metricas['prueba'].items() if k!='matriz_confusion'},name='prueba').to_frame())
matriz=np.array(metricas['prueba']['matriz_confusion'])
fig,ax=plt.subplots(figsize=(5,4)); ax.imshow(matriz,cmap='Blues')
for i in range(2):
    for j in range(2): ax.text(j,i,str(matriz[i,j]),ha='center',va='center',color='white' if matriz[i,j]>matriz.max()/2 else 'black')
ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['Sin alerta','Alerta'],yticklabels=['Legítima','Fraude'],xlabel='Predicción',ylabel='Real',title='Matriz de confusión · prueba temporal')
plt.tight_layout(); plt.show()"""),
code("""from sklearn.metrics import precision_recall_curve
precision,recall,_=precision_recall_curve(predicciones.es_fraude,predicciones.riesgo_estimado)
plt.plot(recall,precision,color='#20647c',label=ganador)
plt.axhline(predicciones.es_fraude.mean(),color='#b55b23',linestyle='--',label='Prevalencia de prueba')
plt.xlabel('Recall'); plt.ylabel('Precisión'); plt.title('Curva precisión–recall · prueba temporal'); plt.legend(); plt.tight_layout(); plt.show()"""),
md('''## 5. Explicar el modelo
La importancia por permutación mide cuánto empeora Average Precision al desordenar una variable, manteniendo las demás. Usamos 2.000 compras de validación y tres repeticiones para limitar tiempo. La desviación refleja variación entre permutaciones, no un intervalo de confianza poblacional.

Las variables correlacionadas pueden compartir señal y aparentar menor importancia. Esto explica dependencia del modelo; no demuestra causas del fraude.'''),
code("""display(importancias.head(10).round(4))
top=importancias.head(10).sort_values('importancia_media')
plt.barh(top.variable,top.importancia_media,xerr=top.desviacion,color='#20647c')
plt.axvline(0,color='#444',linewidth=1); plt.xlabel('Caída de Average Precision'); plt.title('Importancia global por permutación · validación'); plt.tight_layout(); plt.show()"""),
md('''## 6. Verificar la inferencia y priorizar clientes
El pipeline serializado debe devolver los mismos resultados que el modelo en memoria. La prioridad combina número de alertas y riesgo máximo observado; ese máximo no es una probabilidad de fraude del cliente.'''),
code("""bundle=load_model()
recalculadas=predict_features(test,bundle)
assert np.allclose(recalculadas.riesgo_estimado,predicciones.riesgo_estimado)
assert recalculadas.riesgo_estimado.between(0,1).all()
assert set(recalculadas.alerta.unique())<={0,1}
display(rank_customers(recalculadas).head(10))
print('Artefacto listo:', ROOT/'artifacts/modelo_fraude.joblib')"""),
md('''## Entrega y continuación
Abra `guia/index.html` para ejecutar el script por lotes, preparar la tarea de Windows, regenerar el reporte y probar Streamlit/API.

**Evidencia individual:** comparación de modelos, matriz de prueba, tres variables relevantes y una justificación del umbral. Añada una limitación: prevalencia artificial, etiquetas maduras, clientes conocidos o incertidumbre de calibración.

**Prompt para Codex:** «Audita este pipeline. Verifica que imputación y codificación se ajusten solo con entrenamiento, que la selección no use prueba y que el artefacto serializado mantenga las predicciones. Ejecuta las pruebas y explica cualquier fallo».

El entrenamiento y la inferencia son una demostración local. Un despliegue real requiere monitoreo, versionado de datos, control de acceso, estado histórico persistente y validación con datos representativos.''')]
for name,cells in [('01_integracion_limpieza_eda.ipynb',nb1),('02_modelos_validacion.ipynb',nb2)]:
    notebook=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python (.venv taller)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}})
    nbf.validate(notebook); nbf.write(notebook,ROOT/'notebooks'/name)
    print(name,len(cells),'celdas')
