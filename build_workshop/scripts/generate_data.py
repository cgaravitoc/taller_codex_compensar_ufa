"""Synthetic educational fixtures. Run this script, then export_clientes.mjs, then validate_data.py."""
from pathlib import Path
import sys
import json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.python_deps'))
import numpy as np
import pandas as pd
SEED = 20261113
rng = np.random.default_rng(SEED)
N, T = 5000, 200000
for folder in ['data', 'data_dict', 'qa', 'tmp']:
    (ROOT / folder).mkdir(parents=True, exist_ok=True)
schemas = {}

def frame(name, specs):
    schemas[name] = specs
    return pd.DataFrame({key: value[0] for key, value in specs.items()})

def spec(values, description, domain, role='predictor'):
    return values, description, domain, role

ids = np.array([f'CLI{i:05}' for i in range(1, N+1)])
age = rng.integers(21, 76, N)
income = np.round(np.clip(rng.lognormal(np.log(3500000), .65, N), 1400000, 30000000), -3)
limit = np.round(np.clip(income*rng.uniform(.8, 4, N), 2000000, 60000000), -3)
cities = np.array(['Bogota', 'Medellin', 'Cali', 'Barranquilla', 'Bucaramanga', 'Pereira'])
city = rng.choice(cities, N)
tenure = np.minimum(rng.integers(3, 180, N), (age-18)*12)
international_enabled = rng.binomial(1, .82, N)
clients = frame('clientes', {
    'id_cliente': spec(ids, 'Identificador ficticio del cliente y llave primaria.', 'CLI00001..CLI05000', 'llave'),
    'fecha_corte': spec(pd.Timestamp('2025-12-31'), 'Fecha de referencia del perfil, disponible antes de las compras.', '2025-12-31', 'control_temporal'),
    'edad': spec(age, 'Edad al corte.', '21..75 anos'),
    'genero': spec(rng.choice(['F', 'M', 'No_informa'], N, p=[.48,.48,.04]), 'Genero declarado sintetico; usar para auditoria de equidad, excluir del modelo base.', 'F; M; No_informa', 'auditoria'),
    'ciudad_residencia': spec(city, 'Ciudad habitual al corte.', ', '.join(cities)),
    'nivel_educativo': spec(rng.choice(['Secundaria','Tecnico','Universitario','Posgrado'], N), 'Nivel educativo sintetico.', 'Secundaria; Tecnico; Universitario; Posgrado'),
    'ocupacion': spec(rng.choice(['Empleado','Independiente','Pensionado'], N, p=[.6,.3,.1]), 'Ocupacion al corte.', 'Empleado; Independiente; Pensionado'),
    'ingreso_mensual_cop': spec(income, 'Ingreso mensual declarado; faltantes intencionales MCAR del 3%.', 'COP; positivo; vacio = desconocido'),
    'antiguedad_cliente_meses': spec(tenure, 'Meses de vinculacion al corte.', '3..179'),
    'id_tarjeta': spec([f'TAR{i:05}' for i in range(1,N+1)], 'Token ficticio, nunca un numero real de tarjeta. Una tarjeta por cliente.', 'TAR00001..TAR05000', 'llave'),
    'antiguedad_tarjeta_meses': spec(np.maximum(1, (tenure*rng.uniform(.1,1,N)).astype(int)), 'Antiguedad de la unica tarjeta activa al corte.', '1..antiguedad_cliente_meses'),
    'cupo_tarjeta_cop': spec(limit, 'Cupo de referencia al corte; no es saldo disponible en cada compra.', 'COP; 2000000..60000000'),
    'compras_internacionales_habilitadas': spec(international_enabled, 'Permiso de compras internacionales, constante durante la simulacion.', '0=no; 1=si'),
})
clients.loc[rng.choice(N, 150, replace=False), 'ingreso_mensual_cop'] = np.nan
clients.loc[(clients.ocupacion=='Pensionado') & (clients.edad<55), 'ocupacion'] = 'Empleado'

# Exactly 25 bureau features plus identifier and cutoff. Credit risk does not enter fraud score.
credit_risk = rng.beta(2, 5, N)
active = rng.integers(2, 12, N)
cards = np.array([rng.integers(1, min(a, 5)+1) for a in active])
credit_limit = limit + np.round(rng.uniform(0, 20000000, N), -3)
util = np.round(np.clip(.15 + .75*credit_risk + rng.normal(0,.12,N), .01,.98),4)
revolving = np.round(credit_limit*util,2)
total_balance = revolving + np.round(rng.uniform(0,80000000,N),2)
m30 = rng.binomial(active, credit_risk*.35)
m60 = rng.binomial(m30, .45)
m90 = rng.binomial(m60, .45)
queries6 = rng.poisson(1+credit_risk*5)
queries3 = rng.binomial(queries6,.55)
queries1 = rng.binomial(queries3,.4)
hist = np.maximum(tenure, np.minimum((age-18)*12, rng.integers(12,360,N)))
bureau = frame('centrales_riesgo', {
    'id_cliente': spec(ids, 'Cliente al que pertenece el corte.', 'FK clientes.id_cliente', 'llave'),
    'fecha_corte': spec(pd.Timestamp('2025-12-30'), 'Corte del buro disponible al inicio del periodo.', '2025-12-30', 'control_temporal'),
    'score_crediticio': spec(np.clip((850-credit_risk*550+rng.normal(0,35,N)).astype(int),300,950), 'Puntaje crediticio ficticio; no reproduce una central real.', '300..950'),
    'antiguedad_crediticia_meses': spec(hist, 'Meses desde la primera obligacion.', 'meses; positivo'),
    'numero_obligaciones_activas': spec(active, 'Obligaciones activas en todas las entidades.', '2..11'),
    'numero_obligaciones_cerradas': spec(rng.poisson(4,N), 'Obligaciones cerradas acumuladas.', 'entero >=0'),
    'numero_tarjetas_credito': spec(cards, 'Tarjetas en todas las entidades, incluida la del caso.', '1..5; <= obligaciones activas'),
    'numero_creditos_consumo': spec(active-cards, 'Otras obligaciones activas, simplificadas como consumo.', 'entero >=0'),
    'saldo_total_deuda_cop': spec(total_balance, 'Saldo de todas las obligaciones activas.', 'COP >=0'),
    'saldo_rotativo_cop': spec(revolving, 'Saldo utilizado en tarjetas de todas las entidades.', 'COP >=0'),
    'cupo_total_tarjetas_cop': spec(credit_limit, 'Suma de cupos de todas las tarjetas.', 'COP >0'),
    'utilizacion_cupo_tarjetas': spec(util, 'Saldo rotativo dividido entre cupo total.', 'proporcion 0..1'),
    'cuota_mensual_total_cop': spec(np.round(total_balance*rng.uniform(.015,.035,N),2), 'Cuotas mensuales estimadas de todas las obligaciones.', 'COP >=0'),
    'obligaciones_mora_30d': spec(m30, 'Obligaciones activas con al menos 30 dias de mora al corte.', 'entero; >= mora 60d'),
    'obligaciones_mora_60d': spec(m60, 'Obligaciones activas con al menos 60 dias de mora al corte.', 'entero; >= mora 90d'),
    'obligaciones_mora_90d': spec(m90, 'Obligaciones activas con al menos 90 dias de mora al corte.', 'entero >=0'),
    'max_dias_mora_12m': spec(np.where(m90>0, rng.integers(90,181,N), np.where(m60>0,75,np.where(m30>0,45,rng.integers(0,30,N)))), 'Mayor mora observada durante los 12 meses previos al corte.', 'dias 0..180'),
    'eventos_mora_12m': spec(m30+rng.poisson(credit_risk*3), 'Episodios de mora de al menos 30 dias en los ultimos 12 meses.', 'entero >=0'),
    'consultas_buro_1m': spec(queries1, 'Consultas en el mes previo al corte.', 'entero >=0'),
    'consultas_buro_3m': spec(queries3, 'Consultas en los 3 meses previos; incluye 1m.', 'entero >= consultas 1m'),
    'consultas_buro_6m': spec(queries6, 'Consultas en los 6 meses previos; incluye 3m.', 'entero >= consultas 3m'),
    'obligaciones_abiertas_6m': spec(rng.binomial(active,.2), 'Obligaciones activas abiertas durante los 6 meses previos.', 'entero <= obligaciones activas'),
    'obligaciones_reestructuradas': spec(rng.binomial(active,credit_risk*.12), 'Obligaciones activas reestructuradas.', 'entero <= obligaciones activas'),
    'obligaciones_castigadas_historicas': spec(rng.poisson(credit_risk*.2), 'Obligaciones castigadas historicamente, fuera de saldos activos.', 'entero >=0'),
    'saldo_en_mora_cop': spec(np.round(total_balance*(m30/active)*rng.uniform(.1,.6,N),2), 'Saldo en mora asociado a obligaciones con mora de al menos 30 dias.', 'COP >=0; <= saldo total'),
    'proporcion_pagos_puntuales_12m': spec(np.round(np.clip(1-credit_risk*.6-rng.uniform(0,.1,N),0,1),4), 'Proporcion de pagos puntuales en los 12 meses previos.', 'proporcion 0..1'),
    'meses_desde_ultima_mora': spec(np.where(m30>0,0,rng.integers(1,60,N)).astype(float), 'Meses desde ultima mora >=30 dias; vacio indica sin mora registrada.', 'meses >=0; vacio = sin historial de mora'),
})
no_mora = (m30==0) & (bureau.eventos_mora_12m.to_numpy()==0) & (rng.random(N)<.6)
bureau.loc[no_mora, 'meses_desde_ultima_mora'] = np.nan
bureau.loc[(m30==0) & (bureau.eventos_mora_12m>0), 'meses_desde_ultima_mora'] = rng.integers(1,12,((m30==0) & (bureau.eventos_mora_12m>0)).sum())
bureau.loc[(bureau.eventos_mora_12m>0) & (m30==0),'max_dias_mora_12m'] = 45
no_recent = (bureau.eventos_mora_12m==0) & bureau.meses_desde_ultima_mora.notna()
bureau.loc[no_recent,'meses_desde_ultima_mora'] = np.minimum(
    np.maximum(bureau.loc[no_recent,'meses_desde_ultima_mora'],13),
    bureau.loc[no_recent,'antiguedad_crediticia_meses'])
# If the entire history is within 12 months and no mora occurred, there is no last mora.
bureau.loc[(bureau.eventos_mora_12m==0) & (bureau.antiguedad_crediticia_meses<=12), 'meses_desde_ultima_mora'] = np.nan

# Every customer has purchases, with heterogeneous frequency and burst-like activity.
weights = rng.lognormal(0,.7,N); weights /= weights.sum()
ci = np.concatenate([np.arange(N),rng.choice(N,T-N,p=weights)])
seconds = rng.integers(0,181*86400,T)
burst = rng.choice(np.arange(N,T),12000,replace=False)
parent = rng.integers(0,N,len(burst))
ci[burst] = ci[parent]
seconds[burst] = seconds[parent]+rng.integers(1,900,len(burst))
seconds = np.clip(seconds,0,181*86400-1)
ts = pd.Timestamp('2026-01-01')+pd.to_timedelta(seconds,unit='s')
channel = rng.choice(['POS','WEB','APP'],T,p=[.5,.3,.2])
foreign = (rng.random(T)<.12) & (international_enabled[ci]==1)
country = np.where(foreign,rng.choice(['US','MX','ES'],T),'CO')
purchase_city = np.where(country=='US','Miami',np.where(country=='MX','Ciudad_de_Mexico',np.where(country=='ES','Madrid',np.where(rng.random(T)<.85,city[ci],rng.choice(cities,T)))))
merchant_idx = rng.integers(0,600,T)
categories = np.array(['Supermercado','Restaurante','Tecnologia','Viajes','Moda','Servicios'])
category = categories[merchant_idx%6]
habit = rng.lognormal(np.log(100000),.45,N)
amount = np.minimum(np.clip(habit[ci]*rng.lognormal(0,.9,T)*np.where(category=='Viajes',2.3,1),5000,12000000),limit[ci]*.9).round(2)
digital = channel!='POS'
new_device = digital & (rng.random(T)<.24)
device = np.where(digital, np.where(new_device, np.array([f'DEVNEW{i:06}' for i in range(T)]), np.array([f'DEV{i:05}' for i in ci])),None)
use3ds = digital & (rng.random(T)<.55)
auth = np.where(channel=='POS',rng.choice(['CHIP_PIN','CONTACTLESS'],T), np.where(use3ds,'3DS','OTP'))
transactions = frame('transacciones', {
    'id_transaccion': spec([f'TRX{i:07}' for i in range(1,T+1)], 'Identificador de compra, no relacionado con fraude.', 'TRX0000001..TRX0200000', 'llave'),
    'id_cliente': spec(ids[ci], 'Cliente titular de la tarjeta; no implica autoria del fraude.', 'FK clientes.id_cliente', 'llave'),
    'id_tarjeta': spec(clients.id_tarjeta.to_numpy()[ci], 'Token de la tarjeta usada.', 'FK clientes.id_tarjeta', 'llave'),
    'fecha_hora': spec(ts, 'Instante de compra en America/Bogota, sin zona en almacenamiento.', '2026-01-01..2026-06-30', 'control_temporal'),
    'fecha': spec(ts.strftime('%Y-%m-%d'), 'Fecha local derivada de fecha_hora.', 'AAAA-MM-DD', 'redundante'),
    'hora': spec(ts.strftime('%H:%M:%S'), 'Hora local derivada de fecha_hora.', 'HH:MM:SS', 'redundante'),
    'monto_cop': spec(amount, 'Valor de la compra en COP; incluso compras internacionales se liquidan en COP.', 'COP >0'),
    'moneda_liquidacion': spec('COP', 'Moneda de todos los montos; no se simulan conversiones de divisas.', 'COP', 'constante'),
    'id_comercio': spec([f'COM{i:04}' for i in merchant_idx], 'Comercio ficticio, 600 comercios con categoria estable.', 'COM0000..COM0599', 'identificador'),
    'nombre_comercio': spec([f'Comercio_Sintetico_{i:04}' for i in merchant_idx], 'Nombre ficticio de cadena con multiples sucursales o canales.', 'texto', 'redundante'),
    'categoria_comercio': spec(category, 'Categoria estable de la cadena.', ', '.join(categories)),
    'canal': spec(channel, 'Canal de realizacion de la compra.', 'POS; WEB; APP'),
    'pais_compra': spec(country, 'Pais del punto de compra; en canal digital, ubicacion de conexion simulada.', 'CO; US; MX; ES'),
    'ciudad_compra': spec(purchase_city, 'Ciudad de compra o conexion en canales digitales.', 'ciudades colombianas; Miami; Ciudad_de_Mexico; Madrid'),
    'numero_cuotas': spec(rng.choice([1,3,6,12,24],T,p=[.55,.18,.12,.1,.05]), 'Cuotas pactadas.', '1; 3; 6; 12; 24'),
    'id_dispositivo': spec(device, 'Identificador digital ficticio. Vacio en POS: no aplica.', 'DEV/DEVNEW; vacio en POS', 'identificador'),
    'metodo_autenticacion': spec(auth, 'Metodo aplicado antes de aprobar la compra.', 'CHIP_PIN; CONTACTLESS; 3DS; OTP'),
    'uso_3ds': spec(use3ds.astype(int), 'Autenticacion 3DS aplicada.', '0=no; 1=si'),
    'resultado_autenticacion': spec('EXITOSA', 'Solo compras aprobadas; autenticacion exitosa no garantiza legitimidad.', 'EXITOSA', 'constante'),
})
transactions = transactions.sort_values(['fecha_hora','id_transaccion']).reset_index(drop=True)
# Observable prior-history features only; these are not exported to encourage feature engineering.
g = transactions.groupby('id_cliente',sort=False)
prior_mean = g.monto_cop.transform(lambda s: s.shift().expanding().mean())
ratio = transactions.monto_cop / prior_mean.fillna(transactions.monto_cop)
gap = g.fecha_hora.diff().dt.total_seconds().fillna(86400*180)
novel = (~transactions.duplicated(['id_cliente','id_dispositivo'])) & transactions.canal.ne('POS')
home = transactions.id_cliente.map(dict(zip(ids,city)))
hour = transactions.fecha_hora.dt.hour
score = (1.1*transactions.canal.ne('POS').astype(float)
         +1.25*novel.astype(float) + .8*transactions.pais_compra.ne('CO').astype(float)
         + .55*transactions.ciudad_compra.ne(home).astype(float)
         + .9*(hour<6).astype(float) + 1.4*(gap<900).astype(float)
         + 1.25*np.log(ratio.clip(.2,10)) - 1.1*transactions.uso_3ds
         + .7*((hour<6)&novel).astype(float))
# Logistic noise produces overlap. Conditioning on count gives exactly 25%, not independent probabilities.
latent = score.to_numpy()+rng.logistic(0,1.15,T)
label = np.zeros(T,dtype=np.int8)
label[np.argpartition(latent,-50000)[-50000:]] = 1
investigated = (label==1) | (rng.random(T)<.10)
report = transactions.fecha_hora + pd.to_timedelta(rng.integers(1,16,T),unit='D')
report = report.where(investigated)
closed = (report+pd.to_timedelta(rng.integers(1,16,T),unit='D')).where(investigated,transactions.fecha_hora+pd.Timedelta(days=45))
fraud_type = np.where(transactions.canal=='POS',rng.choice(['Tarjeta_sustraida','Clonacion'],T),rng.choice(['Compra_no_presencial','Toma_de_cuenta'],T))
obs = frame('observacion_fraude', {
    'id_transaccion': spec(transactions.id_transaccion, 'Compra seguida; una fila por compra, investigada o cerrada por ventana.', 'FK transacciones.id_transaccion; PK', 'llave'),
    'fue_investigada': spec(investigated.astype(int), 'Si hubo investigacion formal posterior a la compra.', '0=no; 1=si', 'post_evento'),
    'estado_caso': spec(np.where(label==1,'FRAUDE_CONFIRMADO',np.where(investigated,'DESCARTADO','SIN_REPORTE_VENTANA_CERRADA')), 'Resultado al corte de observacion.', 'FRAUDE_CONFIRMADO; DESCARTADO; SIN_REPORTE_VENTANA_CERRADA', 'post_evento'),
    'fecha_reporte': spec(report, 'Instante de apertura de investigacion; vacio si no hubo reporte.', 'posterior a compra; nullable', 'post_evento'),
    'fecha_cierre': spec(closed, 'Resolucion de investigacion o fin de ventana de 45 dias.', 'posterior a compra; <= corte', 'post_evento'),
    'fecha_corte_observacion': spec(pd.Timestamp('2026-08-15'), 'Fecha de consolidacion de etiquetas maduras para todas las compras.', '2026-08-15', 'post_evento'),
    'es_fraude': spec(label, 'Objetivo binario confirmado. Cero por descarte o cierre de ventana bajo supuesto de reporte completo en esta simulacion.', '0=legitima; 1=fraude; exactamente 50000 positivos', 'objetivo'),
    'tipo_fraude': spec(np.where(label==1,fraud_type,'NO_APLICA'), 'Tipologia posterior de investigacion.', 'Tarjeta_sustraida; Clonacion; Compra_no_presencial; Toma_de_cuenta; NO_APLICA', 'post_evento'),
    'perdida_confirmada_cop': spec(np.where(label==1,np.round(transactions.monto_cop*rng.uniform(.35,1,T),2),0), 'Perdida neta simulada despues de recuperaciones; nunca supera monto.', 'COP >=0', 'post_evento'),
})

bureau.to_csv(ROOT/'data/centrales_riesgo.csv',sep=';',index=False,encoding='utf-8',date_format='%Y-%m-%d')
transactions.to_parquet(ROOT/'data/transacciones.parquet',index=False,compression='snappy',engine='pyarrow')
obs.to_csv(ROOT/'data/observacion_fraude.txt',sep='|',index=False,encoding='utf-8',date_format='%Y-%m-%d %H:%M:%S')
# Intermediate only, outside the four workshop inputs.
payload = json.loads(clients.to_json(orient='split',date_format='iso'))
(ROOT/'tmp/clientes.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')

for name, df in [('clientes',clients),('centrales_riesgo',bureau),('transacciones',transactions),('observacion_fraude',obs)]:
    lines = [f'# Diccionario: {name}', '',
             '| Campo | Tipo | Descripcion | Dominio / unidad |',
             '|---|---|---|---|']
    schema = []
    for col in df:
        _, desc, domain, role = schemas[name][col]
        dtype = str(df[col].dtype)
        lines.append(f'| {col} | {dtype} | {desc} | {domain} |')
        schema.append(dict(campo=col,tipo=dtype,descripcion=desc,dominio=domain))
    (ROOT/f'data_dict/{name}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (ROOT/f'data_dict/{name}.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf-8')
from transaction_quality import inject_quality, update_dictionary
transactions = inject_quality(transactions)
transactions.to_parquet(ROOT/'data/transacciones.parquet',index=False,compression='snappy')
update_dictionary(transactions)
print(json.dumps({'clientes':len(clients),'variables_buro':len(bureau.columns)-2,'transacciones':len(transactions),'fraudes':int(label.sum()),'tasa':float(label.mean())}))
