# Diccionario: clientes

| Campo | Tipo | Descripcion | Dominio / unidad |
|---|---|---|---|
| id_cliente | str | Identificador ficticio del cliente y llave primaria. | CLI00001..CLI05000 |
| fecha_corte | datetime64[us] | Fecha de referencia del perfil, disponible antes de las compras. | 2025-12-31 |
| edad | int64 | Edad al corte. | 21..75 anos |
| genero | str | Genero declarado sintetico; usar para auditoria de equidad, excluir del modelo base. | F; M; No_informa |
| ciudad_residencia | str | Ciudad habitual al corte. | Bogota, Medellin, Cali, Barranquilla, Bucaramanga, Pereira |
| nivel_educativo | str | Nivel educativo sintetico. | Secundaria; Tecnico; Universitario; Posgrado |
| ocupacion | str | Ocupacion al corte. | Empleado; Independiente; Pensionado |
| ingreso_mensual_cop | float64 | Ingreso mensual declarado; faltantes intencionales MCAR del 3%. | COP; positivo; vacio = desconocido |
| antiguedad_cliente_meses | int64 | Meses de vinculacion al corte. | 3..179 |
| id_tarjeta | str | Token ficticio, nunca un numero real de tarjeta. Una tarjeta por cliente. | TAR00001..TAR05000 |
| antiguedad_tarjeta_meses | int64 | Antiguedad de la unica tarjeta activa al corte. | 1..antiguedad_cliente_meses |
| cupo_tarjeta_cop | float64 | Cupo de referencia al corte; no es saldo disponible en cada compra. | COP; 2000000..60000000 |
| compras_internacionales_habilitadas | int64 | Permiso de compras internacionales, constante durante la simulacion. | 0=no; 1=si |
