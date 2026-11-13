from pathlib import Path
import re

path=Path(__file__).resolve().parents[1]/'guia/index.html'
html=path.read_text(encoding='utf-8')
def section(name,content):
    global html
    html,n=re.subn(r'<section id="'+name+r'">.*?</section>',lambda _:content,html,flags=re.S)
    assert n==1,name

html=html.replace('Integra datos, construye un modelo y úsalo para priorizar alertas. Tú defines el objetivo, revisas las decisiones y compruebas el código que propone Codex.',
    'Crea tus propios notebooks con Codex, desde la exploración hasta la validación de un modelo. Tú planteas las preguntas, decides qué aceptar y compruebas cada resultado.')
section('preparacion',r'''<section id="preparacion"><div class="eyebrow">Preparación previa · fuera de los 90 minutos</div><h2>Comienza con los datos y una hoja en blanco</h2>
<p><strong>Tu objetivo:</strong> crear dos notebooks propios, comprender su código y defender sus decisiones. Recibes los datos y los diccionarios; la solución la construirás conversando con Codex por etapas.</p>
<ol><li>Abre la raíz del repositorio en VS Code. Ten disponibles las extensiones Python, Jupyter y Codex, y el acceso autorizado por tu organización.</li><li>Prepara Python 3.12 y el entorno antes de la sesión:</li></ol>
<pre><code>py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "import pandas, sklearn; print('Entorno listo')"</code></pre>
<p>Cuando Codex cree un notebook, ábrelo y selecciona <strong>.venv</strong> como kernel. No necesitas activar el entorno para utilizar los comandos anteriores.</p>
<div class="callout decision"><strong>Acuerdo de trabajo.</strong> Los notebooks y scripts resueltos que ya existen son referencias del facilitador. Para la práctica, crea archivos con el prefijo <code>mi_</code>. Pide a Codex trabajar solo con <code>data/</code>, los diccionarios y tus archivos nuevos. No copies las soluciones ni importes sus funciones para presentar el flujo como propio. Los originales permanecen disponibles para una comparación posterior.</div>
<div class="table-wrap"><table><caption>Entradas y entregables que vas a construir</caption><thead><tr><th>Tipo</th><th>Ruta</th><th>Uso</th></tr></thead><tbody>
<tr><td>Entradas</td><td><code>data/</code> y <code>data/data_dict/</code></td><td>Cuatro fuentes y sus diccionarios; conservar sin cambios</td></tr>
<tr><td>Por crear</td><td><code>notebooks/mi_01_eda.ipynb</code></td><td>Lectura, integración, calidad y exploración</td></tr>
<tr><td>Por crear</td><td><code>notebooks/mi_02_modelos.ipynb</code></td><td>Partición, comparación, optimización y validación</td></tr>
<tr><td>Tus salidas</td><td><code>artifacts/mi_taller/</code></td><td>Base preparada, pipeline, métricas y contrato de inferencia</td></tr>
<tr><td>Continuación</td><td><code>python/mi_inferencia.py</code>, <code>reports/mi_reporte.html</code>, <code>app/mi_app.py</code></td><td>Consumir y comunicar tu modelo</td></tr>
<tr><td>Bitácora</td><td><code>mi_entrega.md</code></td><td>Decisiones, prompts relevantes, errores y evidencias</td></tr></tbody></table></div>
<p><strong>Ritmo de la sesión:</strong> contexto 10 min; EDA 25 min; modelos 30 min; scripts 7 min; reporte 7 min; app 8 min; cierre 3 min. La prioridad individual son los dos notebooks ejecutables. Los bloques finales son extensiones guiadas sobre tus resultados; si el tiempo no alcanza, registra lo pendiente y complétalo en casa. No presentes una demostración del facilitador como una ejecución propia.</p>
<details><summary>Datos del caso</summary><p>5.000 clientes, 25 variables de buró por cliente, 200.000 compras y 25% de fraude por diseño. Los datos son sintéticos e incluyen problemas de calidad intencionales. Predice por transacción y agrega alertas por cliente; el titular puede ser la víctima.</p></details>
</section>''')
html=html.replace('Revisa README.md, los diccionarios de data/data_dict y los dos notebooks.\nExplícame el flujo del taller y las llaves de unión. No modifiques archivos todavía.\nSeñala qué variables solo se conocen después de una compra y no deben ser predictores.\nSi no puedes comprobar una afirmación, indícalo.',
'''Voy a construir mis propios notebooks para el caso de fraude.
Trabaja solo con los cuatro insumos de data/, data/data_dict/ y los archivos
mi_ que creemos. No leas ni reutilices notebooks, scripts, modelos, reportes
resueltos, pruebas del facilitador ni build_workshop/.
Primero inspecciona los diccionarios y una muestra acotada de cada fuente.
Explica la unidad de análisis, las llaves y posibles variables posteriores al evento.
Propón un plan breve, sin crear todavía el análisis completo.
Separa lo que comprobaste de lo que estás suponiendo.''')
anchor='<h3>Primer prompt</h3>'
html=html.replace(anchor,'''<h3>Cómo conducir a Codex</h3><p>En cada encargo incluye <strong>contexto + objetivo + archivos permitidos + alcance del paso + restricciones + criterio de aceptación</strong>. Envía un prompt, revisa lo producido, ejecútalo y decide si avanzar. Guarda en tu bitácora una decisión que aceptaste y otra que corregiste.</p>
<div class="table-wrap"><table><thead><tr><th>Momento</th><th>Qué le pides</th><th>Qué haces tú</th></tr></thead><tbody><tr><td>Planear</td><td>Alternativas y supuestos</td><td>Elegir según el caso de negocio</td></tr><tr><td>Construir</td><td>Un bloque de celdas, no todo el proyecto</td><td>Revisar datos, fórmulas y cambios</td></tr><tr><td>Ejecutar</td><td>Usar .venv y mostrar salida o error real</td><td>Confirmar ejecución y resultados</td></tr><tr><td>Validar</td><td>Una comprobación que pueda fallar</td><td>Interpretar si demuestra lo que necesitas</td></tr></tbody></table></div>
<h3>Primer prompt: delimitar contexto y alcance</h3>''')

section('datos',r'''<section id="datos"><div class="eyebrow">02 · Construye tu notebook de EDA</div><h2>De las fuentes a decisiones de preparación</h2><span class="time">Minutos 10–35</span>
<p><strong>Archivo por crear:</strong> <code>notebooks/mi_01_eda.ipynb</code>. Copia los prompts de uno en uno. Ajusta las propuestas de Codex antes de seguir. Cada bloque debe contener propósito, código ejecutable, salida e interpretación escrita por ti.</p>
<h3>1. Crear la estructura y cargar datos · 5 min</h3>
<pre><code>Crea notebooks/mi_01_eda.ipynb desde cero, sin consultar las soluciones existentes.
Incluye objetivo de negocio, unidad de análisis, configuración de rutas y lectura
de los cuatro insumos de data/. Respeta los separadores de los archivos.
Añade celdas pequeñas que muestren filas, columnas, tipos y una muestra acotada.
Usa el entorno .venv. No limpies ni entrenes todavía.
Ejecuta las celdas y guarda las salidas; si no puedes ejecutarlas, explícame
el bloqueo y el comando exacto que debo ejecutar. No inventes resultados.</code></pre>
<p><strong>Revisa tú:</strong> ¿las rutas funcionan desde la raíz y desde el notebook? ¿CSV y TXT se separaron correctamente? ¿Puedes explicar qué representa una fila de cada tabla? Debes observar 5.000 clientes y 200.000 compras, no una única columna por separador incorrecto.</p>
<h3>2. Diseñar y validar las uniones · 4 min</h3>
<pre><code>Amplía mi_01_eda.ipynb con un mapa de relaciones entre las fuentes.
Comprueba nulos, unicidad y registros huérfanos en id_cliente e id_transaccion.
Implementa las uniones con validación explícita de cardinalidad y conserva
las fechas de corte y de cierre necesarias para el siguiente notebook.
Compara filas antes y después. Incluye una prueba que detecte multiplicación
de compras por una llave duplicada. No elimines duplicados para ocultar el problema.</code></pre>
<p><strong>Criterio:</strong> cliente→compras es uno a muchos; compra→observación es uno a uno. La unión debe conservar las 200.000 compras. Una repetición de cliente no es una compra duplicada. Exige evidencia de cobertura, no solo que el código termine.</p>
<h3>3. Diagnosticar antes de limpiar · 4 min</h3>
<pre><code>Perfila la calidad de las transacciones: tipos, formatos inválidos, nulos,
valores fuera de dominio, cuantiles, atípicos y proporción de la categoría dominante.
Distingue nulos estructurales, captura ausente y texto que no se convierte a número.
Muéstrame una tabla problema / evidencia / alternativas / riesgo de cada alternativa.
Todavía no apliques correcciones. No utilices el fraude para decidir qué filas limpiar.</code></pre>
<p><strong>Decide tú:</strong> ¿un monto extremo es imposible o solo poco frecuente? ¿Una columna casi constante está mal o aporta poca información? ¿Qué perderías al eliminar una columna con muchos nulos? No adoptes automáticamente un umbral de 80% o una regla IQR sin explicarlo.</p>
<h3>4. Acordar reglas y aplicarlas · 6 min</h3>
<p>Después de revisar el diagnóstico, completa los corchetes con tus decisiones. Por ejemplo, puedes normalizar formatos inequívocos, dejar nulos los montos ambiguos y contrastar fechas redundantes con el timestamp canónico. Esas decisiones deben quedar justificadas en el notebook.</p>
<pre><code>Aplica al notebook únicamente estas reglas que he elegido:
[escribe aquí problema, regla, justificación y tratamiento si no es recuperable].
Preserva los insumos crudos. Registra filas y valores afectados por cada regla.
No calcules medianas, escaladores ni parámetros de imputación con toda la base:
eso se ajustará dentro del pipeline de entrenamiento.
Si excluyes filas, conserva una tabla de exclusiones y compara la tasa de fraude
antes y después. Añade comprobaciones de dominio y conservación de llaves.</code></pre>
<p><strong>Criterio:</strong> una regla verificable explica qué cambia, por qué y cuántas observaciones afecta. Un valor ambiguo no debe convertirse a cero por comodidad. No necesitas replicar los conteos o decisiones de la solución del facilitador.</p>
<h3>5. EDA orientado a la pregunta y salida · 6 min</h3>
<pre><code>Completa mi_01_eda.ipynb con tres visualizaciones que respondan preguntas
del negocio: volumen y tasa por canal, patrón por hora y distribución de montos.
Incluye denominadores, unidades y cantidad de nulos excluidos. Escribe preguntas
para que yo interprete los resultados, sin afirmar causalidad.
Propón variables disponibles al comprar y documenta su disponibilidad temporal.
Guarda mi base preparada y un resumen de calidad en artifacts/mi_taller/.
Conserva id_transaccion, id_cliente, fecha_hora, es_fraude y fecha_cierre para
la trazabilidad y partición; aclara que no todos serán predictores.
Reinicia el kernel, ejecuta de principio a fin y guarda el notebook con salidas.</code></pre>
<div class="callout decision"><strong>Historia de comportamiento, si alcanza el tiempo:</strong> pide a Codex media de monto previo, tiempo desde la compra anterior y novedad de comercio. Exige que excluya la compra actual y futuras. Comprueba que agregar una compra futura no altere las variables anteriores. Si queda pendiente, comienza con predictores disponibles en la compra y documenta el alcance; no simules una historia que no calculaste.</div>
<p><strong>Interpretación individual:</strong> escribe dos hallazgos sustentados en tus gráficos, una decisión de limpieza y una limitación. El EDA global es descriptivo; evita usar resultados del periodo de prueba para seleccionar predictores o reglas estadísticas. En una evaluación ciega estricta, reserva también ese EDA.</p>
<details><summary>Si Codex se equivoca: prompt de corrección</summary><pre><code>Al ejecutar la celda [número] obtengo este error: [pega el error completo].
Esperaba [resultado verificable]. Explica la causa antes de modificar código.
Corrige solo el bloque afectado, conserva las decisiones acordadas y vuelve
a ejecutar desde un kernel limpio. No suprimas la comprobación que falló.</code></pre></details>
<label class="check"><input type="checkbox" data-step="datos">Creé mi notebook de EDA y puedo justificar su limpieza y hallazgos</label></section>''')

section('modelos',r'''<section id="modelos"><div class="eyebrow">03 · Construye tu notebook de modelos</div><h2>De una comparación justa a un modelo verificable</h2><span class="time">Minutos 35–65</span>
<p><strong>Archivo por crear:</strong> <code>notebooks/mi_02_modelos.ipynb</code>. Usa la base y decisiones de tu notebook 01. No cargues el modelo entrenado del facilitador. El ganador, las métricas y el umbral deben provenir de tu ejecución.</p>
<h3>1. Diseñar la evaluación antes de entrenar · 5 min</h3>
<pre><code>Lee mi_01_eda.ipynb y mis salidas en artifacts/mi_taller/.
Propón el diseño de mi_02_modelos.ipynb: objetivo binario, predictores candidatos,
variables excluidas y particiones temporales de entrenamiento, validación y prueba.
Comprueba cuándo estaban disponibles perfiles, variables y etiquetas.
Considera la maduración de las etiquetas: no selecciones solo fraudes que se
confirmaron rápido mientras excluyes compras legítimas aún no maduras.
Muestra fechas, tamaños y tasas de cada partición propuesta. No entrenes todavía.
Explica si la evaluación responde a compras nuevas de clientes conocidos o a clientes nuevos.</code></pre>
<p><strong>Decide tú:</strong> qué momento simulas, qué etiqueta estaba disponible y qué población evaluas. Puedes usar una ventana de maduración común para que todos los ejemplos de entrenamiento tengan seguimiento suficiente.</p>
<details><summary>Ejemplo de calendario defendible, no obligatorio</summary><p>Entrenamiento con compras anteriores al 15 de febrero y etiquetas disponibles al 1 de abril: así se completan 45 días para todas esas compras. Validación con compras de abril, maduras antes del 16 de junio. Prueba con compras del 16 al 30 de junio y etiquetas consolidadas al 15 de agosto. Los intervalos restantes pueden aportar historia de compras, pero no ajustes con etiquetas futuras. Verifica estas condiciones con los datos, no solo con el calendario.</p></details>
<h3>2. Crear el notebook y el pipeline · 5 min</h3>
<pre><code>Crea notebooks/mi_02_modelos.ipynb con el diseño temporal que acordamos:
[indica fechas, criterio de maduración y predictores aceptados].
Incluye secciones de objetivo, datos, partición, pipeline, comparación,
optimización, prueba, explicación y exportación. Implementa primero hasta pipeline.
Ajusta imputación, escalado y codificación solo con entrenamiento.
Excluye IDs, etiqueta y campos posteriores a la compra de los predictores.
Incluye pruebas de separación temporal, llaves disjuntas entre particiones
y disponibilidad de las etiquetas. Ejecuta y muéstrame los resultados.</code></pre>
<p><strong>Criterio:</strong> transformar validación/prueba no significa ajustar el preprocesamiento con ellas. Inspecciona dónde aparece <code>fit</code>. No basta con excluir una columna llamada “fraude”: también revisa sus derivados y los campos posteriores a la investigación.</p>
<h3>3. Comparar alternativas con una referencia · 6 min</h3>
<pre><code>Añade una referencia Dummy y dos clasificadores de familias distintas,
por ejemplo regresión logística y boosting. Usa las mismas particiones y
predictores para comparar. Fija semillas y limita el cómputo para el taller.
Reporta en validación Average Precision, ROC-AUC, precisión, recall y tiempo.
Explica qué aporta cada métrica y qué umbral usas para precisión/recall.
No calcules aún las métricas de prueba. Ejecuta y guarda la comparación.</code></pre>
<p><strong>Revisa tú:</strong> ¿hay mejora sobre la referencia trivial? ¿Qué cuesta un falso negativo y qué carga genera un falso positivo? No elijas solo por accuracy. Average Precision resume precisión–recall y no equivale exactamente a su área trapezoidal.</p>
<h3>4. Optimizar y elegir umbral · 5 min</h3>
<pre><code>Propón dos configuraciones adicionales de un modelo prometedor y explica
qué cambia cada hiperparámetro. Evalúalas solo en validación.
Usa como criterio principal [métrica que he elegido y por qué].
Propón un umbral según [presupuesto de alertas o compromiso precisión/recall].
Muestra el efecto en validación y deja registrados modelo, parámetros y umbral
congelados antes de abrir prueba. No busques hasta obtener una métrica deseada.</code></pre>
<p><strong>Decide tú:</strong> el criterio operativo. Un presupuesto de 20% de alertas es una opción didáctica, no una regla obligatoria. Usar repetidamente validación también puede sobreajustarla; acota la búsqueda y conserva prueba para el cierre.</p>
<h3>5. Evaluar y explicar · 5 min</h3>
<pre><code>Con el modelo y umbral congelados, evalúa una vez el periodo de prueba.
Genera matriz de confusión, curva precisión–recall y métricas con denominadores.
Calcula importancia por permutación sobre una muestra de validación y explica
sus límites. No atribuyas causalidad ni autoría de fraude al titular.
Guarda tablas y gráficos de mi ejecución. Si el resultado es bajo, repórtalo;
no ajustes el modelo con prueba para presentarlo como una evaluación independiente.</code></pre>
<p><strong>Interpretación individual:</strong> explica el compromiso entre falsos positivos y negativos, tres variables relevantes y un límite de generalización. La prevalencia del 25% es artificial; el score no queda calibrado para fraude real por haber terminado el entrenamiento.</p>
<h3>6. Exportar y demostrar reproducibilidad · 4 min</h3>
<pre><code>Exporta mi pipeline, lista y orden de predictores, tipos esperados, umbral,
versión y reglas de limpieza a artifacts/mi_taller/. Documenta el contrato
en contrato_inferencia.json e incluye un lote de ejemplo sin la etiqueta.
Comprueba que cargar el modelo guardado produce las mismas predicciones que
el modelo en memoria. Prueba una categoría nueva y una entrada inválida.
Reinicia el kernel y ejecuta el notebook de principio a fin. Guarda las salidas
y registra cualquier comprobación pendiente en mi_entrega.md.</code></pre>
<div class="callout"><strong>Criterio de cierre:</strong> tus notebooks funcionan en orden desde un kernel limpio, tus métricas vienen de salidas ejecutadas y puedes justificar partición, modelo y umbral. No necesitas obtener el mismo ganador ni las mismas métricas que el facilitador.</div>
<label class="check"><input type="checkbox" data-step="modelos">Creé y ejecuté mi notebook de modelos y validé sus decisiones</label></section>''')

section('automatizacion',r'''<section id="automatizacion"><div class="eyebrow">04 · Extensión guiada de tu trabajo</div><h2>Convertir tu notebook en inferencia automatizable</h2><span class="time">Minutos 65–72</span>
<p>Parte de tu pipeline y de <code>artifacts/mi_taller/contrato_inferencia.json</code>. Los scripts resueltos del repositorio no necesariamente aceptan tu modelo; no mezcles artefactos de distintas ejecuciones.</p>
<pre><code>A partir de mis notebooks y de mi contrato de inferencia, crea
python/mi_inferencia.py. Extrae mis funciones reutilizables a un módulo propio
y actualiza mis notebooks para usarlas sin cambiar las predicciones.
El script debe cargar mi pipeline sin reentrenar, aceptar rutas de entrada/salida,
aplicar las mismas reglas y exportar id_transaccion, id_cliente, score y alerta.
No debe requerir es_fraude ni datos de investigación para predecir.
Si usé historia, exige los registros previos necesarios y evita mirar el futuro.
Añade logs y salida distinta de cero si falla. Ejecuta mi lote de ejemplo
y compara sus predicciones con las de mi notebook.</code></pre>
<p><strong>Revisa:</strong> rutas, dependencias, tratamiento de faltantes y equivalencia de predicción. Pide a Codex el comando exacto según los argumentos que realmente creó.</p>
<pre><code>Crea python/mi_programar_tarea.bat para ejecutar mi script diariamente en
Windows. Incluye --dry-run: debe mostrar ejecutable, argumentos, carpeta y hora
sin registrar la tarea. Usa .venv, maneja rutas con espacios y no almacenes claves.
No sobrescribas tareas existentes. Ejecuta solo --dry-run y explícame cómo
registrar, inspeccionar y eliminar la tarea cuando yo decida activarla.</code></pre>
<pre><code>.\python\mi_programar_tarea.bat --dry-run</code></pre>
<p>Ejecuta el comando únicamente después de que el BAT exista. La automatización de un archivo fijo no implementa llegada de datos nuevos ni mantenimiento de historia. Documenta esas diferencias.</p>
<label class="check"><input type="checkbox" data-step="automatizacion">Creé inferencia para mi modelo y comprobé el dry-run</label></section>''')

section('reporte',r'''<section id="reporte"><div class="eyebrow">05 · Comunica tu evidencia</div><h2>Pedir a Codex un reporte a partir de tus resultados</h2><span class="time">Minutos 72–79</span>
<p>El reporte debe utilizar tus salidas de EDA y modelos. No copies las cifras del reporte resuelto. Decide primero qué necesita entender quien revisa alertas.</p>
<pre><code>Construye reports/mi_reporte.html usando únicamente los resultados ejecutados
de mis notebooks y artifacts/mi_taller/. Incluye calidad antes/después, EDA,
comparación en validación, métricas de prueba y explicabilidad del modelo.
Añade interacciones útiles, como filtro de canal o simulador de umbral.
Documenta fuente, periodo, unidades y denominadores de cada vista.
Si simulas otro umbral sobre prueba, márcalo como exploración retrospectiva:
no debe cambiar mi modelo ni presentarse como optimización independiente.
Propón una implementación que pueda regenerar con las dependencias acordadas.
Entrega el generador y sus comandos. No inventes resultados si falta un artefacto.</code></pre>
<p><strong>Revisa:</strong> coteja al menos una tasa, una celda de la matriz y una importancia contra tu notebook. Cambia un filtro, comprueba el denominador y verifica el restablecimiento. Las explicaciones son del modelo, no causas demostradas del fraude.</p>
<div class="callout"><strong>Alcance mínimo:</strong> un HTML con EDA y explicación global de tu modelo, más una interacción comprobada. Puedes ampliar la priorización por cliente después. Si reutilizas una plantilla visual del facilitador, cambia todas las fuentes y resultados y registra esa reutilización.</div>
<label class="check"><input type="checkbox" data-step="reporte">Generé un reporte con mis resultados y comprobé una interacción</label></section>''')

section('app',r'''<section id="app"><div class="eyebrow">06 · Consume tu modelo</div><h2>Crear una interfaz Streamlit con Codex</h2><span class="time">Minutos 79–87</span>
<p>La aplicación debe respetar tu contrato de inferencia. Antes de pedir un formulario, identifica qué datos vienen del usuario y cuáles deben calcularse desde perfiles e historia.</p>
<pre><code>Crea app/mi_app.py en Streamlit para consumir mi pipeline y el servicio de
predicción que extrajimos de mis notebooks. No cargues el modelo del facilitador.
Deriva los campos del formulario de mi contrato de inferencia y valida sus dominios.
Busca perfiles e historia necesaria; no pidas al usuario inventar variables históricas.
Muestra score, umbral, alerta y una explicación de su alcance. Maneja entradas
inválidas con mensajes claros y permite descargar el resultado.
No entrenes al abrir la app ni consultes información posterior al evento.
Prueba una compra válida y otra inválida; indica si las llamadas persisten historia.</code></pre>
<pre><code>.\.venv\Scripts\python.exe -m streamlit run app\mi_app.py --server.address 127.0.0.1</code></pre>
<p><strong>Revisa tú:</strong> usa el mismo ejemplo que en el script y compara scores. Comprueba un cliente desconocido, un monto inválido y los datos faltantes. Un formulario que abre no demuestra equivalencia con entrenamiento.</p>
<details><summary>Ampliación para casa: una API HTTP</summary><p>Streamlit es la interfaz web; una API es un contrato para otros sistemas.</p><pre><code>Expón mi servicio compartido en app/mi_api.py con FastAPI: GET /health y
POST /predict. Define esquema, validaciones y respuesta según mi contrato.
Prueba una solicitud válida y dos inválidas. Devuelve errores claros, carga
solo mi artefacto confiable y documenta inicio local y limitaciones de estado.
No publiques el servicio.</code></pre><p>Comprueba la misma predicción en notebook, script y API. Define qué faltaría para autenticación, persistencia y monitoreo antes de hablar de un servicio de producción.</p></details>
<label class="check"><input type="checkbox" data-step="app">Creé una interfaz para mi modelo y contrasté sus predicciones</label></section>''')

html=html.replace('Tu entrega de sesión reúne los dos notebooks con salidas, el reporte HTML, el modelo y una inferencia de ejemplo.',
    'Tu entrega mínima de sesión reúne <code>mi_01_eda.ipynb</code> y <code>mi_02_modelos.ipynb</code>, creados por ti con Codex, con salidas ejecutadas, tu pipeline y tus decisiones. Adjunta las extensiones que completaste (script, reporte y app) y señala explícitamente lo pendiente.')
html=html.replace('<h3>Verificación final</h3><pre><code>.\\.venv\\Scripts\\python.exe -m pytest tests -q</code></pre><p>Las pruebas cubren limpieza, llaves, historia causal, etiquetas temporales, categorías nuevas, pipeline y API. Ejecutar pruebas no sustituye interpretar los resultados.</p>',
'''<h3>Auditoría final con Codex</h3><pre><code>Audita únicamente mis notebooks y archivos mi_. Crea pruebas en tests/mi_taller/
para los contratos que realmente implementé: llaves, limpieza, disponibilidad
temporal, ausencia de fuga y equivalencia de inferencia. Ejecuta las pruebas.
Comprueba que las salidas del notebook no estén obsoletas. Resume qué pasó,
qué falló y qué no se ejecutó, con evidencia. No cambies decisiones ni debilites
las pruebas para ocultar un fallo.</code></pre><p>Las pruebas del facilitador verifican su solución, no la tuya. Conserva el comando de ejecución de tus propias pruebas y explica qué error detectaría cada una.</p>''')
html=html.replace('Cómo usaste Codex, qué errores detectaste y qué verificaste.',
    'Cómo usaste Codex: prompt inicial, una respuesta que corregiste, decisión propia y evidencia de verificación.')
section('problemas',r'''<section id="problemas"><h2>Cómo recuperar el control cuando algo falla</h2>
<details><summary>Codex genera todo el taller de una vez</summary><p>Acota el encargo: «Detente después del diagnóstico. No crees todavía el modelo ni la app. Muéstrame los supuestos y espera mi decisión de limpieza». Trabaja en bloques revisables.</p></details>
<details><summary>Codex usa una solución resuelta</summary><p>Reitera los archivos permitidos y pide retirar imports o dependencias del facilitador. Revisa los imports y rutas. No basta con renombrar un notebook existente para que constituya tu construcción.</p></details>
<details><summary>No ejecuta el notebook o afirma resultados sin salida</summary><p>Pide el intérprete utilizado, la celda ejecutada y la salida real. Selecciona .venv, reinicia el kernel y ejecuta todas las celdas. Marca como pendiente cualquier resultado que no puedas reproducir.</p></details>
<details><summary>Falla una celda</summary><p>Comparte el error completo, el bloque afectado y el resultado esperado. Pide diagnóstico y corrección mínima. No elimines la comprobación que detectó el problema.</p></details>
<details><summary>Las métricas parecen demasiado buenas</summary><p>Busca etiquetas o derivados entre predictores, particiones solapadas, preprocesamiento ajustado con prueba, historia futura y duplicados. Pide pruebas de esos riesgos antes de celebrar el resultado.</p></details>
<details><summary>Mi modelo no encaja en los scripts existentes</summary><p>Esos scripts pertenecen a la referencia del facilitador. Usa tu contrato para crear o adaptar tus archivos mi_. Verifica predictores, tipos, limpieza, historia y formato del artefacto; no cambies solo la ruta del modelo.</p></details>
<details><summary>No alcanza el tiempo</summary><p>Prioriza notebooks pequeños, una referencia, dos clasificadores y una búsqueda acotada. Conserva evidencia de qué ejecutaste. Los scripts, reporte y app pueden completarse con la misma guía en casa; el facilitador puede demostrar su referencia sin sustituir tu entrega.</p></details>
<details><summary>El reporte o la app no inicia</summary><p>Pide a Codex revisar las dependencias y comandos de tu implementación. Comprueba que tu artefacto exista y que el puerto esté libre. No presentes el reporte o la app del facilitador como resultado de tu modelo.</p></details>
</section>''')
html=html.replace("'codex-taller-avance'","'codex-taller-autoria-v2'")
path.write_text(html,encoding='utf-8')
assert 'Abre <a href="../notebooks/' not in html
assert html.count('data-step=')==7
print('Guía actualizada: creación por etapas, prompts, decisiones y criterios propios.')
