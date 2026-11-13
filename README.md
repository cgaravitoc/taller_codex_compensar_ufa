# Taller Codex en VS Code · Analítica de fraude

**Empieza por [guia/index.html](guia/index.html).** Contiene el tutorial detallado, agenda de 90 minutos, prompts para Codex, decisiones, comandos, verificaciones y desafío para casa.

## Preparación

Python 3.12, VS Code con extensiones Python/Jupyter/Codex. Desde la raíz, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Selecciona `.venv` como kernel. No necesitas activar el entorno. La instalación se hace antes de la sesión.

## Recorrido

1. Ejecuta `notebooks/01_integracion_limpieza_eda.ipynb`.
2. Ejecuta `notebooks/02_modelos_validacion.ipynb`.
3. Ejecuta `.\.venv\Scripts\python.exe python\inferencia.py`.
4. Revisa `.\python\programar_tarea.bat --dry-run`. Ejecutar el BAT sin ese argumento registra una tarea diaria; no está activada por la entrega de estos archivos.
5. Abre `reports/reporte_fraude.html`.
6. Ejecuta `.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py`.
7. Opcional: `.\.venv\Scripts\python.exe -m uvicorn app.api:app --host 127.0.0.1 --port 8000` y abre `/docs`.
8. Comprueba `.\.venv\Scripts\python.exe -m pytest tests -q`.

Para reconstruir entrenamiento sin notebook: `.\.venv\Scripts\python.exe python\entrenar.py`.
Para regenerar el reporte: `.\.venv\Scripts\python.exe python\generar_reporte.py` (requiere Node y el plugin Data de Codex; `DATA_PLUGIN_ROOT` permite indicar su ubicación). El HTML entregado es autocontenido y se abre sin esas dependencias. `--solo-datos` actualiza evidencia, no el HTML.

## Archivos

- `data/`: copia verificada de los cuatro insumos crudos. `data/data_dict/`: solo los cuatro diccionarios Markdown.
- `guia/`: tutorial HTML.
- `notebooks/`: dos cuadernos con resultados guardados.
- `python/`: limpieza/historia compartidas, entrenamiento, inferencia, servicio y programación de Windows.
- `app/`: Streamlit y API FastAPI opcional. Ambos usan el mismo servicio; Streamlit no requiere iniciar la API.
- `artifacts/`: base preparada, pipeline serializado, métricas, importancias y predicciones de prueba.
- `reports/`: reporte HTML, fuente editable y salidas de inferencia.
- `tests/`: comprobaciones de limpieza, causalidad temporal, pipeline y API.
- `qa/`: evidencia de ejecución y revisión.
- `build_workshop/`: construcción original de los datos, incluida referencia limpia del facilitador. No se usa para entrenar ni inferir.

## Supuestos que debes conservar

200.000 transacciones, 5.000 clientes y 25% de fraude sintético. Predicción por transacción y priorización posterior por cliente. No inferir que el titular cometió fraude.

La captura contiene defectos intencionales. Se preservan filas; montos inválidos pasan a nulo y se imputan dentro del pipeline con entrenamiento. La historia utiliza solo compras anteriores. Entrenamiento usa etiquetas cerradas antes del 1 de abril; validación es abril y prueba del 16 al 30 de junio. El umbral se selecciona en validación. El EDA global es descriptivo y no selecciona hiperparámetros. La prueba evalúa clientes conocidos, no clientes nuevos.

El modelo no está calibrado ni validado para fraude real. La app/API son locales, sin persistencia ni autenticación. La tarea de Windows ejecuta un lote fijo; no implementa ingestión incremental. Carga únicamente artefactos joblib propios y confiables.
