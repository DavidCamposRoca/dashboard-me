import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración profesional
st.set_page_config(page_title="BI Mundo Estudiante", layout="wide")

# Nombre exacto de tu archivo subido
FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    # Cargamos las pestañas
    leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
    inv = pd.read_excel(FILE, sheet_name='Inversion')
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    return leads, inv

try:
    df_leads, df_inv = load_data()

    st.title("📊 Dashboard de Marketing - Mundo Estudiante")
    
    # --- FILTROS ---
    with st.sidebar:
        st.header("Filtros")
        centros = st.multiselect("Centros", options=df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        
    df_f = df_leads[df_leads['Centro origen'].isin(centros)]

    # --- KPIs ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Leads Totales", f"{len(df_f):,}")
    c2.metric("Inversión Total", f"{df_inv['INVERSIÓN TOTAL'].sum():,.2f} €")
    c3.metric("Captados", f"{len(df_f[df_f['Situacion actual'] == 'CLIENTE CAPTADO'])}")

    st.markdown("---")

    # --- GRÁFICOS ---
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Leads por Centro")
        fig1 = px.bar(df_f['Centro origen'].value_counts().reset_index(), x='Centro origen', y='count', color='Centro origen')
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_b:
        st.subheader("Inversión por Canal")
        canales = ['INVERSIÓN EN G ADS', 'INVERSIÓN EN META', 'INVERSIÓN EN TIKTOK', 'INVERSIÓN AFILIACION']
        inversion_canales = df_inv[canales].sum().reset_index()
        inversion_canales.columns = ['Canal', 'Inversión']
        fig2 = px.pie(inversion_canales, values='Inversión', names='Canal', hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
