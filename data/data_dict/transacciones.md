# Diccionario: transacciones

| Campo | Tipo | Descripcion | Dominio / unidad |
|---|---|---|---|
| id_transaccion | str | Identificador de compra, no relacionado con fraude. | TRX0000001..TRX0200000 |
| id_cliente | str | Cliente titular de la tarjeta; no implica autoria del fraude. | FK clientes.id_cliente |
| id_tarjeta | str | Token de la tarjeta usada. | FK clientes.id_tarjeta |
| fecha_hora | datetime64[us] | Instante de compra en America/Bogota, sin zona en almacenamiento. | 2026-01-01..2026-06-30 |
| fecha | str | Fecha local derivada de fecha_hora. Contiene 1500 fechas DD/MM/AAAA y 1500 fechas imposibles. fecha_hora conserva el instante canonico para contraste. | AAAA-MM-DD |
| hora | str | Hora local derivada de fecha_hora. Contiene 1000 horas imposibles. fecha_hora conserva el instante canonico para contraste. | HH:MM:SS |
| monto_cop | string | Valor de la compra en COP; incluso compras internacionales se liquidan en COP. Captura cruda almacenada como texto: 4000 formatos no canonicos, 1000 errores de escala, 500 negativos y 500 ceros. Requiere normalizacion y validacion. | COP >0 |
| moneda_liquidacion | str | Moneda de todos los montos; no se simulan conversiones de divisas. | COP |
| id_comercio | str | Comercio ficticio, 600 comercios con categoria estable. | COM0000..COM0599 |
| nombre_comercio | str | Nombre ficticio de cadena con multiples sucursales o canales. | texto |
| categoria_comercio | str | Categoria estable de la cadena. | Supermercado, Restaurante, Tecnologia, Viajes, Moda, Servicios |
| canal | str | Canal de realizacion de la compra. Contiene 2000 registros con espacios y minusculas; normalizar antes de evaluar el dominio. | POS; WEB; APP |
| pais_compra | str | Pais del punto de compra; en canal digital, ubicacion de conexion simulada. | CO; US; MX; ES |
| ciudad_compra | str | Ciudad de compra o conexion en canales digitales. | ciudades colombianas; Miami; Ciudad_de_Mexico; Madrid |
| numero_cuotas | int64 | Cuotas pactadas. | 1; 3; 6; 12; 24 |
| id_dispositivo | str | Identificador digital ficticio. Vacio en POS: no aplica. | DEV/DEVNEW; vacio en POS |
| metodo_autenticacion | str | Metodo aplicado antes de aprobar la compra. | CHIP_PIN; CONTACTLESS; 3DS; OTP |
| uso_3ds | int64 | Autenticacion 3DS aplicada. | 0=no; 1=si |
| resultado_autenticacion | str | Solo compras aprobadas; autenticacion exitosa no garantiza legitimidad. | EXITOSA |
| latencia_red_ms | float64 | Latencia de red observada al autorizar. Falta por perdida simulada de telemetria, no por no aplicabilidad. | Milisegundos >0; 85% nulos exactos |
| version_sdk | string | Version del SDK de captura de telemetria. Ausencia de captura simulada. | 2.1.0; 2.2.0; 2.3.0; 95% nulos exactos |
| sistema_origen | str | Sistema que envia el registro. Variable categorica casi constante. | CORE_TARJETAS 99.5%; PASARELA_LEGACY 0.5% |
| indicador_reintento | int8 | Indica si hubo un reintento tecnico antes de completar la compra. | 0=99.9%; 1=0.1% |
