# Ejercicio de calidad de transacciones

El Parquet de `data/` es ahora una captura cruda con defectos intencionales: **200.000 filas y 23 columnas**. Conserva `id_cliente`, `id_transaccion`, `id_tarjeta` y `fecha_hora` completos e intactos. Los otros tres insumos y las 50.000 etiquetas de fraude permanecen iguales.

## Catálogo para el facilitador

Todos los porcentajes tienen como denominador las 200.000 transacciones. Los grupos dentro de monto son excluyentes; los defectos entre columnas pueden coincidir en una misma fila.

| Problema | Columna | Cantidad | Porcentaje | Ejemplo / tratamiento a discutir |
|---|---|---:|---:|---|
| Moneda y separadores locales | monto_cop | 2.000 | 1% | `COP 123.456,78`: normalizar explícitamente |
| Texto sin monto recuperable | monto_cop | 1.000 | 0,5% | `no_disponible`: convertir a nulo, nunca a cero por defecto |
| Letra O en lugar de dígito | monto_cop | 1.000 | 0,5% | `1O0O`: error ambiguo, revisar o poner en cuarentena |
| Error de escala extremo | monto_cop | 1.000 | 0,5% | Monto original × 100 + 100 millones COP; supera el cupo |
| Monto negativo | monto_cop | 500 | 0,25% | Inválido: esta base solo incluye compras, no devoluciones |
| Monto cero | monto_cop | 500 | 0,25% | Inválido para este contrato de compras |
| Fecha en otro formato | fecha | 1.500 | 0,75% | `DD/MM/AAAA`: parseo explícito con día primero |
| Fecha imposible | fecha | 1.500 | 0,75% | `2026-02-30`: contrastar con fecha_hora |
| Hora imposible | hora | 1.000 | 0,5% | `25:61:99`: contrastar con fecha_hora |
| Categorías inconsistentes | canal | 2.000 | 1% | ` web `: quitar espacios y homogeneizar mayúsculas |
| Alta ausencia de telemetría | latencia_red_ms | 170.000 nulos | 85% | Evaluar cobertura antes de imputar o excluir |
| Alta ausencia de telemetría | version_sdk | 190.000 nulos | 95% | Distinguir falta de captura de categoría real |
| Variable casi constante | sistema_origen | 199.000 CORE_TARJETAS | 99,5% | Otros 1.000: PASARELA_LEGACY |
| Variable binaria casi constante | indicador_reintento | 199.800 ceros | 99,9% | Otros 200: unos; varianza poblacional 0,000999 |

También siguen presentes dos constantes originales: `moneda_liquidacion=COP` y `resultado_autenticacion=EXITOSA`. Los nulos de `id_dispositivo` en POS son estructurales (no aplica), a diferencia de los nuevos nulos de telemetría.

## Cómo interpretar los atípicos

Los 1.000 extremos introducidos son errores de captura conocidos por construcción. La distribución original también contiene compras grandes válidas. Una regla IQR puede marcar otros registros; eso no demuestra que sean errores ni fraude. No eliminar automáticamente todas las observaciones atípicas. Evaluar consistencia con cupo, canal y contexto, y documentar la decisión.

## Almacenamiento y entrenamiento

Parquet conserva tipos por columna. Para alojar símbolos monetarios y texto erróneo, **monto_cop pasó de número a string en toda la columna**. El archivo no está roto: `read_parquet` funciona, pero las operaciones numéricas requieren limpieza. `fecha_hora` sigue siendo un timestamp canónico y permite comprobar o reconstruir las columnas redundantes `fecha` y `hora`.

La etiqueta se generó antes de corromper los datos. Los defectos usan otra semilla y no consultan `es_fraude`: no representan señales causales de fraude. Una pérdida confirmada puede superar un monto crudo inválido; validar esa relación solo después de tratar el error. La tasa global sigue en 25%, pero eliminar filas puede cambiarla: reportar conteos y tasas antes y después de limpiar.

No se añade una bandera de error al insumo de participantes. Los archivos en `qa/facilitador/` son referencia de corrección y no deben incorporarse como predictores ni usarse para sustituir silenciosamente la limpieza:

- `transacciones_original.parquet`: referencia anterior a los defectos, 19 columnas.
- `defectos_inyectados.csv`: 12.000 celdas modificadas en columnas existentes, con llave, problema y valor anterior/posterior. No enumera nulos ni categorías de las cuatro columnas nuevas.

`qa/calidad_transacciones.json` registra los conteos comprobados sobre el Parquet guardado. `qa/validacion.json` distingue las verificaciones del crudo de las reglas de negocio sobre la referencia limpia. Un contrato didáctico aprobado no significa que el crudo esté listo para modelar.

## Reproducción

`generate_data.py` ya incluye esta etapa, después de generar las etiquetas. Para reaplicar únicamente los defectos a la referencia original:

```powershell
python build_workshop/scripts/transaction_quality.py
python build_workshop/scripts/validate_data.py
```

La ejecución es idempotente: parte de la referencia limpia y no acumula corrupción sobre una versión ya contaminada. Semilla de calidad: 20261114.
