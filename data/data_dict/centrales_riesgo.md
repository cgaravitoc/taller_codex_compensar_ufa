# Diccionario: centrales_riesgo

| Campo | Tipo | Descripcion | Dominio / unidad |
|---|---|---|---|
| id_cliente | str | Cliente al que pertenece el corte. | FK clientes.id_cliente |
| fecha_corte | datetime64[us] | Corte del buro disponible al inicio del periodo. | 2025-12-30 |
| score_crediticio | int64 | Puntaje crediticio ficticio; no reproduce una central real. | 300..950 |
| antiguedad_crediticia_meses | int64 | Meses desde la primera obligacion. | meses; positivo |
| numero_obligaciones_activas | int64 | Obligaciones activas en todas las entidades. | 2..11 |
| numero_obligaciones_cerradas | int64 | Obligaciones cerradas acumuladas. | entero >=0 |
| numero_tarjetas_credito | int64 | Tarjetas en todas las entidades, incluida la del caso. | 1..5; <= obligaciones activas |
| numero_creditos_consumo | int64 | Otras obligaciones activas, simplificadas como consumo. | entero >=0 |
| saldo_total_deuda_cop | float64 | Saldo de todas las obligaciones activas. | COP >=0 |
| saldo_rotativo_cop | float64 | Saldo utilizado en tarjetas de todas las entidades. | COP >=0 |
| cupo_total_tarjetas_cop | float64 | Suma de cupos de todas las tarjetas. | COP >0 |
| utilizacion_cupo_tarjetas | float64 | Saldo rotativo dividido entre cupo total. | proporcion 0..1 |
| cuota_mensual_total_cop | float64 | Cuotas mensuales estimadas de todas las obligaciones. | COP >=0 |
| obligaciones_mora_30d | int64 | Obligaciones activas con al menos 30 dias de mora al corte. | entero; >= mora 60d |
| obligaciones_mora_60d | int64 | Obligaciones activas con al menos 60 dias de mora al corte. | entero; >= mora 90d |
| obligaciones_mora_90d | int64 | Obligaciones activas con al menos 90 dias de mora al corte. | entero >=0 |
| max_dias_mora_12m | int64 | Mayor mora observada durante los 12 meses previos al corte. | dias 0..180 |
| eventos_mora_12m | int64 | Episodios de mora de al menos 30 dias en los ultimos 12 meses. | entero >=0 |
| consultas_buro_1m | int64 | Consultas en el mes previo al corte. | entero >=0 |
| consultas_buro_3m | int64 | Consultas en los 3 meses previos; incluye 1m. | entero >= consultas 1m |
| consultas_buro_6m | int64 | Consultas en los 6 meses previos; incluye 3m. | entero >= consultas 3m |
| obligaciones_abiertas_6m | int64 | Obligaciones activas abiertas durante los 6 meses previos. | entero <= obligaciones activas |
| obligaciones_reestructuradas | int64 | Obligaciones activas reestructuradas. | entero <= obligaciones activas |
| obligaciones_castigadas_historicas | int64 | Obligaciones castigadas historicamente, fuera de saldos activos. | entero >=0 |
| saldo_en_mora_cop | float64 | Saldo en mora asociado a obligaciones con mora de al menos 30 dias. | COP >=0; <= saldo total |
| proporcion_pagos_puntuales_12m | float64 | Proporcion de pagos puntuales en los 12 meses previos. | proporcion 0..1 |
| meses_desde_ultima_mora | float64 | Meses desde ultima mora >=30 dias; vacio indica sin mora registrada. | meses >=0; vacio = sin historial de mora |
