import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Mundo Estudiante - Google Ads Performance", layout="wide")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
    inv = pd.read_excel(FILE, sheet_name='Inversion')
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- LÓGICA DE IDENTIFICACIÓN G ADS ---
    # Marcamos como GAds si tiene GCLID o si la columna SEM/SEO dice 'SEM'
    df_leads['es_gads'] = (df_leads['GCLID'].notnull()) | (df_leads['SEM / SEO'] == 'SEM')

    st.title("🎯 Rendimiento Específico: Google Ads")
    
    # --- FILTROS ---
    with st.sidebar:
        st.header("Configuración")
        lista_meses = sorted(df_leads['MES_AÑO'].unique(), reverse=True)
        periodo = st.selectbox("Seleccionar Periodo", ["Todos"] + lista_meses)
        centros = st.multiselect("Centros", options=df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())

    # Aplicar Filtros
    df_f_leads = df_leads[df_leads['Centro origen'].isin(centros)]
    df_f_inv = df_inv
    if periodo != "Todos":
        df_f_leads = df_f_leads[df_f_leads['MES_AÑO'] == periodo]
        df_f_inv = df_inv[df_inv['MES_AÑO'] == periodo]

    # Datos filtrados SOLO para Google Ads
    gads_leads = df_f_leads[df_f_leads['es_gads'] == True]
    
    # --- CÁLCULOS G ADS ---
    n_leads = len(gads_leads)
    n_clientes = len(gads_leads[gads_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
    inv_gads = df_f_inv['INVERSIÓN EN G ADS'].sum()
    ingresos_gads = gads_leads['Valor total'].sum()

    # Métricas calculadas
    cr = (n_clientes / n_leads * 100) if n_leads > 0 else 0
    cpl = (inv_gads / n_leads) if n_leads > 0 else 0
    cpa = (inv_gads / n_clientes) if n_clientes > 0 else 0
    roas = (ingresos_gads / inv_gads) if inv_gads > 0 else 0

    # --- VISUALIZACIÓN KPIs ---
    st.subheader(f"Métricas Google Ads - {periodo}")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    c1.metric("Leads G Ads", f"{n_leads}")
    c2.metric("Clientes (Captados)", f"{n_clientes}")
    c3.metric("CPL (Coste Lead)", f"{cpl:.2f} €")
    c4.metric("CR (Tasa Conv.)", f"{cr:.1f}%")
    c5.metric("ROAS", f"{roas:.2f}x")

    st.markdown("---")

    col_izq, col_der = st.columns(2)

    with col_izq:
        st.write("### 💸 Inversión vs Ingresos G Ads")
        df_money = pd.DataFrame({
            'Concepto': ['Inversión G Ads', 'Ingresos Generados'],
            'Euros': [inv_gads, ingresos_gads]
        })
        fig_money = px.bar(df_money, x='Concepto', y='Euros', color='Concepto', text_auto='.2s')
        st.plotly_chart(fig_money, use_container_width=True)

    with col_der:
        st.write("### 🏢 Leads G Ads por Centro")
        fig_centro = px.pie(gads_leads, names='Centro origen', hole=0.4)
        st.plotly_chart(fig_centro, use_container_width=True)

    # --- TABLA DE CAUSAS DE PÉRDIDA ---
    st.write("### ❌ ¿Por qué perdemos leads de Google Ads?")
    perdidios = gads_leads[gads_leads['Situacion actual'] == 'CLIENTE PERDIDO']
    causas = perdidios['Causa perdido'].value_counts().reset_index()
    fig_causas = px.bar(causas, x='count', y='Causa perdido', orientation='h', title="Top Causas de Perdida")
    st.plotly_chart(fig_causas, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
