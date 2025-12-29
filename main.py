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
    
    # Aseguramos que el periodo sea formato fecha
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    
    # Creamos una columna de texto para el selector (Ej: "2025-10")
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    st.title("📊 Dashboard de Marketing - Mundo Estudiante")
    
    # --- BARRA LATERAL (FILTROS) ---
    with st.sidebar:
        st.header("🔍 Filtros de Análisis")
        
        # 1. Filtro de Periodo - AHORA ES UN DESPLEGABLE
        lista_meses = sorted(df_leads['MES_AÑO'].unique(), reverse=True)
        opciones_periodo = ["Todos los meses"] + lista_meses
        
        periodo_seleccionado = st.selectbox(
            "Selecciona el Periodo",
            options=opciones_periodo
        )
        
        # 2. Filtro de Centros
        centros = st.multiselect(
            "Seleccionar Centros", 
            options=df_leads['Centro origen'].unique(), 
            default=df_leads['Centro origen'].unique()
        )

    # --- APLICAR FILTROS A LOS DATOS ---
    if periodo_seleccionado == "Todos los meses":
        df_f_leads = df_leads[df_leads['Centro origen'].isin(centros)]
        df_f_inv = df_inv
    else:
        df_f_leads = df_leads[(df_leads['MES_AÑO'] == periodo_seleccionado) & (df_leads['Centro origen'].isin(centros))]
        df_f_inv = df_inv[df_inv['MES_AÑO'] == periodo_seleccionado]

    # --- MÉTRICAS (KPIs) ---
    c1, c2, c3, c4 = st.columns(4)
    
    total_l = len(df_f_leads)
    inv_t = df_f_inv['INVERSIÓN TOTAL'].sum()
    captados = len(df_f_leads[df_f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
    cpl = inv_t / total_l if total_l > 0 else 0

    c1.metric("Leads", f"{total_l:,}")
    c2.metric("Inversión", f"{inv_t:,.2f} €")
    c3.metric("Clientes Captados", f"{captados}")
    c4.metric("CPL (Coste/Lead)", f"{cpl:.2f} €")

    st.markdown("---")

    # --- GRÁFICOS ---
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Captación por Centro")
        fig1 = px.bar(
            df_f_leads['Centro origen'].value_counts().reset_index(), 
            x='Centro origen', y='count', 
            color='Centro origen',
            text_auto=True
        )
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_b:
        st.subheader("Inversión por Canal")
        canales = ['INVERSIÓN EN G ADS', 'INVERSIÓN EN META', 'INVERSIÓN EN TIKTOK', 'INVERSIÓN AFILIACION']
        inv_canales = df_f_inv[canales].sum().reset_index()
        inv_canales.columns = ['Canal', 'Euros']
        fig2 = px.pie(inv_canales, values='Euros', names='Canal', hole=0.5)
        st.plotly_chart(fig2, use_container_width=True)

    # --- EVOLUCIÓN TEMPORAL ---
    st.subheader("Evolución Mensual")
    evolucion = df_f_leads.groupby('MES_AÑO').size().reset_index(name='Cantidad')
    # Ordenar para que la línea de tiempo tenga sentido
    evolucion = evolucion.sort_values('MES_AÑO')
    fig3 = px.line(evolucion, x='MES_AÑO', y='Cantidad', markers=True, title="Tendencia de Leads")
    st.plotly_chart(fig3, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
