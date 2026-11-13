import React, {useState} from 'react';
import {useDataApp, EvidenceChart, DataComponent, DataTable, RichNarrative} from '../../data-app-public.jsx';
import './workshop.css';

export function ReportContent(){
  const {reviewedRows}=useDataApp();
  const summary=reviewedRows('summary')[0];
  const [channel,setChannel]=useState('Todos');
  const [exploratoryThreshold,setThreshold]=useState(null);
  if(!summary) return <p>Ejecute los notebooks y regenere la evidencia del reporte.</p>;
  const fmt=new Intl.NumberFormat('es-CO');
  const pct=v=>(v*100).toFixed(1)+'%';
  const monthly=reviewedRows('monthly').filter(r=>channel==='Todos'||r.canal===channel);
  const test=reviewedRows('test');
  const threshold=exploratoryThreshold??summary.umbral;
  const positives=test.filter(r=>r.es_fraude===1).length;
  const alerts=test.filter(r=>r.riesgo_estimado>=threshold);
  const tp=alerts.filter(r=>r.es_fraude===1).length;
  const fp=alerts.length-tp, fn=positives-tp, tn=test.length-positives-fp;
  const importance=reviewedRows('importance').slice(0,10);
  const narrative=(id,value)=><RichNarrative id={id} value={value}/>;
  return <article className="report-page fraud-report">
    {narrative('intro',`# Fraude sintético: de la calidad a las alertas\n\nLaboratorio de analítica con Codex · Compras de enero a junio de 2026 · Etiquetas consolidadas al 15 de agosto.`)}
    <DataComponent id="summary-evidence" queryId="summary" title="Lectura del caso" sourceRows={[summary]}>
      {narrative('summary-text',`## Lo que muestran los resultados\n\nLa base contiene **${fmt.format(summary.compras)} compras** de **${fmt.format(summary.clientes)} clientes**. El **${pct(summary.fraudRate)} de fraude** es una proporción sintética impuesta para el taller.\n\nEl modelo **${summary.modelo}**, elegido con validación, alcanza **${summary.average_precision.toFixed(3)} de Average Precision** en prueba temporal. Con el umbral congelado de **${summary.umbral.toFixed(3)}**, detecta **${pct(summary.recall)} de los fraudes** y **${pct(summary.precision)} de las alertas corresponden a fraude**.\n\nEl puntaje sirve para priorizar revisión de compras y clientes. No demuestra causalidad, autoría del fraude ni rendimiento sobre datos reales.`)}
    </DataComponent>
    {narrative('quality-intro','## 1. Calidad antes de modelar\n\nLa captura incluye errores intencionales. Se recuperaron formatos inequívocos; los montos imposibles se dejaron nulos para imputar con entrenamiento. Las filas se conservaron. La ausencia de dispositivo en POS significa “no aplica”; los nulos de telemetría representan falta de captura.')}
    <EvidenceChart id="null-coverage" queryId="nulls" title="Proporción de nulos físicos en la captura" rows={reviewedRows('nulls').slice(0,8)} sourceRows={reviewedRows('nulls')} spec={{type:'horizontalBar',x:'campo',y:'nullRate'}} height={340}/>
    <DataComponent id="quality-decisions" queryId="quality" title="Reglas aplicadas y filas afectadas" sourceRows={reviewedRows('quality')}>
      <DataTable rows={reviewedRows('quality')} columns={[{key:'regla',label:'Regla'},{key:'cantidad',label:'Cantidad'}]} searchable={false} caption="Resultados de limpieza"/>
    </DataComponent>
    {narrative('eda-intro','## 2. Comportamientos asociados\n\nEstas vistas describen el conjunto completo. El modelo se seleccionó con particiones temporales independientes. Un patrón observado en estos datos reproduce parcialmente las reglas sintéticas, no una conclusión sobre una población real.')}
    <label className="fraud-control">Canal para la evolución mensual <select value={channel} onChange={e=>setChannel(e.target.value)}>{['Todos','POS','WEB','APP'].map(v=><option key={v}>{v}</option>)}</select></label>
    <EvidenceChart id="monthly-fraud" queryId="monthly" title="Tasa de fraude mensual por canal" rows={monthly} sourceRows={monthly} spec={{type:'line',x:'mes',y:'fraudRate',series:'canal',stackable:false}} height={320}/>
    <EvidenceChart id="hourly-fraud" queryId="hours" title="Tasa de fraude por hora local" rows={reviewedRows('hours')} sourceRows={reviewedRows('hours')} spec={{type:'line',x:'hora',y:'fraudRate',xLabel:'Hora · America/Bogota'}} height={300}/>
    {narrative('models-intro','## 3. Comparación y prueba temporal\n\nEntrenamiento utiliza solo etiquetas conocidas antes del 1 de abril. Validación corresponde a abril y estaba madura al congelar la selección el 16 de junio. Prueba abarca del 16 al 30 de junio. Los periodos intermedios aportan historia de compras, no ajustes al modelo.\n\nAverage Precision resume precisión–recall; la comparación usa validación. La prueba mide compras futuras de clientes conocidos. Las probabilidades no están calibradas para otra prevalencia.')}
    <EvidenceChart id="model-comparison" queryId="comparison" title="Average Precision en validación" rows={reviewedRows('comparison')} sourceRows={reviewedRows('comparison')} spec={{type:'horizontalBar',x:'modelo',y:'average_precision',valueDecimals:3}} height={300}/>
    <DataComponent id="validation-table" queryId="comparison" title="Métricas de candidatos · umbral 0,5" sourceRows={reviewedRows('comparison')}>
      <DataTable rows={reviewedRows('comparison')} columns={[{key:'modelo',label:'Modelo'},{key:'average_precision',label:'Average Precision'},{key:'roc_auc',label:'ROC-AUC'},{key:'precision',label:'Precisión'},{key:'recall',label:'Recall'}]} searchable={false} caption="Comparación en validación"/>
    </DataComponent>
    {narrative('explain-intro','## 4. Explicabilidad global\n\nLa importancia mide la caída de Average Precision al desordenar una variable en 2.000 compras de validación, con tres repeticiones. Valores mayores indican mayor dependencia del modelo. Las variables correlacionadas pueden compartir importancia. No es una atribución causal ni una explicación individual de una alerta.')}
    <EvidenceChart id="permutation" queryId="importance" title="Importancia por permutación · caída de Average Precision" rows={importance} sourceRows={reviewedRows('importance')} spec={{type:'horizontalBar',x:'etiqueta',y:'importancia_media',valueDecimals:3}} height={440}/>
    <DataComponent id="importance-table" queryId="importance" title="Variación entre permutaciones" sourceRows={reviewedRows('importance')}>
      <DataTable rows={reviewedRows('importance')} columns={[{key:'variable',label:'Variable'},{key:'importancia_media',label:'Caída media AP'},{key:'desviacion',label:'Desviación entre repeticiones'}]} caption="Importancias del modelo"/>
    </DataComponent>
    {narrative('threshold-intro','## 5. Explorar el costo de alertar\n\nEl umbral entregado se eligió para alertar aproximadamente el 20% de validación. Muévalo para entender precisión, cobertura y carga de revisión en prueba. Esta simulación es retrospectiva: no autoriza escoger un nuevo umbral usando prueba ni modifica el modelo guardado.')}
    <DataComponent id="threshold-simulation" queryId="test" title="Simulador de umbral · prueba temporal" sourceRows={test}>
      <div className="fraud-control"><label htmlFor="threshold">Umbral exploratorio: {threshold.toFixed(3)}</label><input id="threshold" aria-label="Umbral exploratorio" type="range" min="0" max="1" step="0.001" value={threshold} onChange={e=>setThreshold(Number(e.target.value))}/><button onClick={()=>setThreshold(null)}>Restablecer umbral del modelo</button></div>
      <div className="fraud-metrics" data-reviewed-rows><p><strong>{fmt.format(alerts.length)}</strong> alertas de {fmt.format(test.length)} compras</p><p><strong>{pct(alerts.length?tp/alerts.length:0)}</strong> precisión</p><p><strong>{pct(positives?tp/positives:0)}</strong> recall</p></div>
      <table className="fraud-matrix" data-reviewed-rows><caption>Matriz de confusión para el umbral exploratorio</caption><thead><tr><th>Real / predicción</th><th>Sin alerta</th><th>Alerta</th></tr></thead><tbody><tr><th>Legítima</th><td>{fmt.format(tn)}</td><td>{fmt.format(fp)}</td></tr><tr><th>Fraude</th><td>{fmt.format(fn)}</td><td>{fmt.format(tp)}</td></tr></tbody></table>
    </DataComponent>
    {narrative('priority-intro','## 6. Clientes a priorizar\n\nLa siguiente lista mantiene el umbral original del modelo. Ordena primero por número de alertas y luego por riesgo máximo entre las compras de prueba. El riesgo máximo es un criterio de prioridad, no la probabilidad de que el cliente cometa fraude. El monto observado omite montos inválidos; no es una pérdida estimada.')}
    <DataComponent id="priority-customers" queryId="ranking" title="Prioridad de revisión · umbral original" sourceRows={reviewedRows('ranking')}>
      <DataTable rows={reviewedRows('ranking')} columns={[{key:'id_cliente',label:'Cliente'},{key:'alertas',label:'Alertas'},{key:'riesgo_maximo',label:'Riesgo máximo'},{key:'transacciones',label:'Compras'},{key:'monto_observado_cop',label:'Monto válido COP'}]} caption="Clientes priorizados"/>
    </DataComponent>
    {narrative('closing','## Alcance del entregable\n\nEl reporte enlaza limpieza, EDA, evaluación e interpretación sobre evidencia sintética. El siguiente paso es reproducir el flujo con otro caso de negocio y documentar decisiones, errores detectados y verificaciones. Para uso real faltan validación externa, calibración, monitoreo, controles operativos y una política de revisión de alertas.')}
  </article>
}
