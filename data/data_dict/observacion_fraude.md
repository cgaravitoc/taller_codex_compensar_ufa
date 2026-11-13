# Diccionario: observacion_fraude

| Campo | Tipo | Descripcion | Dominio / unidad |
|---|---|---|---|
| id_transaccion | str | Compra seguida; una fila por compra, investigada o cerrada por ventana. | FK transacciones.id_transaccion; PK |
| fue_investigada | int64 | Si hubo investigacion formal posterior a la compra. | 0=no; 1=si |
| estado_caso | str | Resultado al corte de observacion. | FRAUDE_CONFIRMADO; DESCARTADO; SIN_REPORTE_VENTANA_CERRADA |
| fecha_reporte | datetime64[us] | Instante de apertura de investigacion; vacio si no hubo reporte. | posterior a compra; nullable |
| fecha_cierre | datetime64[us] | Resolucion de investigacion o fin de ventana de 45 dias. | posterior a compra; <= corte |
| fecha_corte_observacion | datetime64[us] | Fecha de consolidacion de etiquetas maduras para todas las compras. | 2026-08-15 |
| es_fraude | int8 | Objetivo binario confirmado. Cero por descarte o cierre de ventana bajo supuesto de reporte completo en esta simulacion. | 0=legitima; 1=fraude; exactamente 50000 positivos |
| tipo_fraude | str | Tipologia posterior de investigacion. | Tarjeta_sustraida; Clonacion; Compra_no_presencial; Toma_de_cuenta; NO_APLICA |
| perdida_confirmada_cop | float64 | Perdida neta simulada despues de recuperaciones; nunca supera monto. | COP >=0 |
