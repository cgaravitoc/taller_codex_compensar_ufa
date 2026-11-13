"""Interfaz local. Streamlit consume el mismo servicio Python que la API HTTP."""
from pathlib import Path
import sys
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
import pandas as pd
import streamlit as st
from taller import ROOT
from servicio import context,score_transaction

st.set_page_config(page_title='Radar de fraude · Taller Codex',page_icon='🔎',layout='wide')
st.title('Radar de fraude')
st.caption('Laboratorio con datos sintéticos · Inferencia individual con historial previo')
if not (ROOT/'artifacts/modelo_fraude.joblib').exists():
    st.error('Falta el modelo. Ejecute notebooks/02_modelos_validacion.ipynb o python/entrenar.py.'); st.stop()
bundle,clients,_,_=context()
st.info('El puntaje ayuda a priorizar revisión. No identifica al titular como autor del fraude ni representa una probabilidad validada en población real.')
left,right=st.columns([1.35,1])
with left:
    st.subheader('Simular una compra')
    customer=st.selectbox('Cliente',clients.id_cliente.tolist())
    profile=clients[clients.id_cliente==customer].iloc[0]
    st.caption(f'Cupo de referencia: COP {profile.cupo_tarjeta_cop:,.0f} · Ciudad habitual: {profile.ciudad_residencia}')
    with st.form('compra'):
        tx=st.text_input('ID nuevo de transacción','DEMO-001')
        when=st.text_input('Fecha y hora local (AAAA-MM-DD HH:MM:SS)','2026-07-01 02:30:00')
        amount=st.number_input('Monto (COP)',min_value=1.,max_value=60000000.,value=350000.,step=10000.)
        channel=st.selectbox('Canal',['WEB','APP','POS'])
        category=st.selectbox('Categoría',['Tecnologia','Supermercado','Restaurante','Viajes','Moda','Servicios'])
        merchant=st.text_input('ID comercio','COM_NUEVO')
        country=st.selectbox('País',['CO','US','MX','ES'])
        city=st.text_input('Ciudad de compra',str(profile.ciudad_residencia))
        cuotas=st.selectbox('Cuotas',[1,3,6,12,24])
        authentication=st.selectbox('Autenticación (POS: CHIP_PIN/CONTACTLESS; digital: OTP/3DS)',['OTP','3DS','CHIP_PIN','CONTACTLESS'])
        device=st.text_input('ID dispositivo digital','DEV_DEMO_NUEVO')
        submit=st.form_submit_button('Evaluar transacción',type='primary')
    if submit:
        try:
            result=score_transaction(dict(id_transaccion=tx,id_cliente=customer,fecha_hora=when,monto_cop=amount,
                canal=channel,categoria_comercio=category,id_comercio=merchant,pais_compra=country,
                ciudad_compra=city,numero_cuotas=cuotas,metodo_autenticacion=authentication,id_dispositivo=device))
            st.session_state['resultado']=result
        except (ValueError,KeyError) as e:
            st.session_state.pop('resultado',None); st.error(str(e))
with right:
    st.subheader('Resultado de la última evaluación')
    if 'resultado' in st.session_state:
        r=st.session_state['resultado']
        st.caption(f"Compra {r['id_transaccion']} · Cliente {r['id_cliente']}")
        st.metric('Riesgo estimado',f"{r['riesgo_estimado']:.1%}")
        st.metric('Umbral del modelo',f"{r['umbral']:.1%}")
        if r['alerta']:
            st.warning('Priorizar para revisión')
        else:
            st.success('No supera el umbral; no garantiza ausencia de fraude')
        st.write('Compras anteriores consultadas:',r['compras_previas_consultadas'])
        st.json(r['contexto'])
        st.caption('Contexto observado de la compra; no es una atribución causal ni una explicación SHAP.')
        st.download_button('Descargar resultado JSON',__import__('json').dumps(r,ensure_ascii=False,indent=2),'inferencia.json','application/json')
    else: st.write('Complete el formulario y pulse Evaluar transacción.')
    st.divider()
    st.subheader('Variables relevantes para el modelo')
    imp=pd.read_csv(ROOT/'artifacts/importancia_permutacion.csv').head(8).set_index('variable')['importancia_media']
    st.bar_chart(imp,horizontal=True)
    st.caption('Importancia global: pérdida de Average Precision al permutar cada variable en una muestra de validación. No explica por sí sola esta compra.')
st.caption('Demostración local sin persistencia, autenticación ni reentrenamiento automático. La API opcional está en app/api.py; Streamlit llama directamente al servicio compartido.')
