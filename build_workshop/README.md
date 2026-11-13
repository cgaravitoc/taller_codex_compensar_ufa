# Insumos sintéticos: detección de fraude en compras con tarjeta

Caso didáctico del taller Codex en VS Code. Todos los registros, clientes, comercios y eventos son ficticios. Semilla: **20261113**. No contiene nombres, documentos, teléfonos, direcciones ni números reales de tarjeta.

## Archivos para participantes

| Archivo en `data/` | Filas | Granularidad / lectura |
|---|---:|---|
| clientes.xlsx | 5.000 | Una fila por cliente; hoja `Clientes`; 13 columnas |
| centrales_riesgo.csv | 5.000 | Un corte por cliente; separador `;`; 25 variables de buró + llave + fecha |
| transacciones.parquet | 200.000 | Una fila por compra aprobada; 23 columnas con defectos intencionales; compresión Snappy |
| observacion_fraude.txt | 200.000 | Una fila por compra seguida; separador `\|`; 9 columnas |

CSV y TXT usan UTF-8, cabecera y punto decimal, sin separadores de miles. Los vacíos representan nulos. Las fechas del Excel son fechas nativas y `fecha_hora` en Parquet es timestamp. En el Parquet, `monto_cop` se almacena ahora como texto y las columnas redundantes `fecha` y `hora` incluyen formatos inconsistentes e imposibles como ejercicio. Toda hora canónica corresponde a America/Bogota (UTC-05), almacenada sin zona.

**Antes del EDA numérico y del modelado, limpiar y validar las transacciones.** El catálogo [calidad_transacciones.md](qa/facilitador/calidad_transacciones.md) detalla formatos defectuosos, montos extremos/inválidos, alta nulidad y variables casi constantes. `qa/facilitador/` contiene una referencia limpia y la bitácora para el instructor, fuera de los cuatro insumos de participantes.

Los diccionarios en `data_dict/` están disponibles en Markdown y JSON e incluyen únicamente Campo, Tipo, Descripcion y Dominio / unidad. El tipo `object` de pandas corresponde a texto en estos archivos. JSON es útil para controles automatizados.

## Relaciones y tiempo

- `clientes.id_cliente` → `centrales_riesgo.id_cliente`: uno a uno en este corte.
- `clientes.id_cliente` → `transacciones.id_cliente`: uno a muchos.
- `transacciones.id_transaccion` → `observacion_fraude.id_transaccion`: uno a uno.
- Una tarjeta del emisor por cliente. Las tarjetas del buró incluyen otras entidades; su número puede ser mayor que uno.
- Perfil de clientes: 31 de diciembre de 2025. Buró: 30 de diciembre de 2025. Se asume que ambos estaban disponibles antes de las compras y permanecen como referencia estática.
- Compras: 1 de enero a 30 de junio de 2026. Etiquetas consolidadas: 15 de agosto de 2026. No se simulan intentos rechazados ni un libro contable de pagos y saldo disponible.

## Objetivo, seguimiento y supuestos

**50.000 fraudes / 200.000 transacciones = 25% exacto.** Es una prevalencia didáctica elegida, no una estimación de fraude real. El desbalance es moderado (3:1), no extremo. Las métricas y probabilidades no deben extrapolarse a otra prevalencia sin evaluación.

El TXT extiende la tabla de investigaciones con el seguimiento de las compras sin reporte, para conservar el universo y evitar completar etiquetas faltantes con cero sin justificación:

- `FRAUDE_CONFIRMADO`: investigación positiva, `es_fraude=1`.
- `DESCARTADO`: investigación negativa, `es_fraude=0`.
- `SIN_REPORTE_VENTANA_CERRADA`: 45 días completos de seguimiento, `es_fraude=0` bajo el supuesto explícito de que todo fraude sintético es reportado y confirmado en un máximo de 30 días.

La verdad sintética se genera primero y determina las investigaciones: todos los positivos se investigan, además de aproximadamente 10% de los negativos. No hay casos pendientes al corte. En una aplicación real, ausencia de reporte no prueba legitimidad; aquí la equivalencia depende del supuesto controlado de simulación. `es_fraude` conserva la verdad sintética, y el generador permite reconstruirla.

## Señal para aprender y limitaciones

La asignación de fraude combina canal digital, novedad de dispositivo, ubicación, horario, cercanía a la compra anterior y desviación del monto respecto al promedio previo. Añade interacciones y ruido logístico, y selecciona los 50.000 valores latentes más altos. No es una regla determinista observable ni una probabilidad calibrada. Hay solapamiento entre clases. Los identificadores se asignan antes de las etiquetas.

El puntaje de generación no utiliza género ni variables de buró. El riesgo crediticio se simula por separado. Pueden aparecer asociaciones indirectas o aleatorias; una asociación no demuestra causalidad ni que el titular haya cometido fraude. El género se reserva para auditoría, fuera del modelo base.

Se incluyen ráfagas de compras, clientes con distinta frecuencia, 600 cadenas comerciales y señales de autenticación. Los comercios son cadenas con sucursales/canales en distintas ubicaciones. Todas las compras se liquidan en COP. Los montos originales no superan el cupo de referencia individual; los errores de captura introducidos sí pueden hacerlo. No se pretende verificar disponibilidad acumulada entre compras.

Faltantes intencionales: 150 ingresos (3%, selección aleatoria), meses desde última mora cuando no hay mora registrada y dispositivo en POS porque no aplica. En transacciones también hay 85% de nulos en latencia de red y 95% en versión del SDK. No hay duplicados de llaves ni clientes huérfanos. Las 50.000 etiquetas se conservan: los defectos se introducen después de generar el fraude, con una semilla independiente.

## Uso durante el taller

```python
from pathlib import Path
import pandas as pd

p = Path('build_workshop/data')  # ejecutar desde la raíz del repositorio
clientes = pd.read_excel(p / 'clientes.xlsx', sheet_name='Clientes')
buro = pd.read_csv(p / 'centrales_riesgo.csv', sep=';', parse_dates=['fecha_corte'])
compras = pd.read_parquet(p / 'transacciones.parquet')
observacion = pd.read_csv(p / 'observacion_fraude.txt', sep='|')
base = compras.merge(clientes, on=['id_cliente', 'id_tarjeta'], validate='many_to_one')
base = base.merge(buro, on='id_cliente', suffixes=('_cliente', '_buro'), validate='many_to_one')
base = base.merge(observacion[['id_transaccion', 'es_fraude']], on='id_transaccion', validate='one_to_one')
assert len(base) == 200_000
```

Derivar variables históricas por cliente ordenando por `fecha_hora`: compras previas en una hora, monto previo en 24 horas, media de montos previos, tiempo desde última compra, comercio y dispositivo vistos previamente. Excluir la compra actual de ventanas históricas; no usar promedios del periodo completo. Los primeros registros tienen historia desconocida, no necesariamente riesgo alto. En POS, dispositivo nuevo no aplica.

Excluir del conjunto de predictores **todas** las columnas de observación, salvo `es_fraude` que es la variable objetivo. Excluir identificadores, campos duplicados y constantes del modelo base. Ajustar imputación, codificación y selección de variables únicamente con entrenamiento. Comparar con un modelo sencillo y evaluar precisión, recall, PR-AUC y alertas al presupuesto disponible.

Para evaluación temporal retrospectiva, separar entrenamiento, validación y prueba por fecha. Para simular un despliegue histórico, exigir además que `fecha_cierre` de cada etiqueta de entrenamiento sea anterior al instante de entrenamiento; incorporar un intervalo de maduración si hace falta. La base consolidada no implica que todas las etiquetas fueran conocidas en junio. Una evaluación por cliente responde a otra pregunta: generalizar a clientes nuevos.

Priorizar clientes agregando las alertas por transacción (por ejemplo, máximo riesgo y monto alertado). No interpretar la suma de probabilidades como probabilidad de fraude del cliente. Las explicaciones del modelo describirán patrones sintéticos aprendidos, no descubrimientos sobre población real.

## Reproducción y controles

Los archivos finales están listos: los asistentes solo necesitan las dependencias de `requirements.txt` para leerlos. Los scripts de construcción están fuera de `data/`.

Para reconstruir desde la raíz del repositorio, en un entorno Python con las dependencias instaladas:

```powershell
python build_workshop/scripts/generate_data.py
node build_workshop/scripts/export_clientes.mjs
python build_workshop/scripts/validate_data.py
```

El exportador de Excel usa `@oai/artifact-tool` del runtime de Codex. Si está en otra ubicación, configurar `ARTIFACT_NODE_ROOT` con la carpeta que contiene su `node_modules`. La reproducción del contenido requiere la misma semilla y versiones; el ZIP del Excel no garantiza identidad binaria. Los comandos sobrescriben los insumos generados de esta carpeta.

`qa/validacion.json` registra los controles ejecutados, conteos, tasas y SHA-256 de los cuatro archivos. `qa/` contiene además vistas de revisión del Excel. `tmp/` y `.python_deps/` son auxiliares locales excluidos de Git; no se necesitan para consumir los insumos.
