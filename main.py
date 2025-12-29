import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página con tema ancho
st.set_page_config(page_title="Mundo Estudiante - Master BI", layout="wide", initial_sidebar_state="expanded")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
    inv = pd.read_excel(FILE, sheet_name='Inversion')
    
    # Formateo de fechas
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

    # --- LÓGICA DE SEGMENTACIÓN ---
    # Google Ads
    leads['Canal_Final'] = 'Otros'
    mask_gads = (leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False))
    leads.loc[mask_gads, 'Canal_Final'] = 'Google Ads'
    
    # Meta (FB/IG)
    mask_meta = (leads['URL'].str.contains('meta|facebook', case=False, na=False)) | \
                (leads['Telekos'].str.contains('facebook', case=False, na=False))
    leads.loc[mask_meta, 'Canal_Final'] = 'Meta Ads'
    
    # SEO
    mask_seo = (leads['GCLID'].isnull()) & \
               (~leads['URL'].str.contains('meta|tiktok|gads|gad_|gbraid|wbraid', case=False, na=False)) & \
               (leads['SEM / SEO'] == 'SEO')
    leads.loc[mask_seo, 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- BARRA LATERAL CON SELECTORES AVANZADOS ---
    with st.sidebar:
        st.image("https://www.mundoestudiante.com/wp-content/uploads/2020/09/logo-mundo-estudiante.png", width=200)
        st.title("Centro de Control")
        
        mes_sel = st.selectbox("📅 Periodo Temporal", ["Todo el Histórico"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True))
        centro_sel = st.multiselect("📍 Centros", options=df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Canal de Captación", options=['Google Ads', 'Meta Ads', 'SEO', 'Otros'], default=['Google Ads', 'Meta Ads', 'SEO', 'Otros'])
        
        st.markdown("---")
        st.caption("v2.0 - Dashboard Escalable")

    # --- FILTRADO DE DATOS ---
    f_leads = df_leads[
        (df_leads['Centro origen'].isin(centro_sel)) & 
        (df_leads['Canal_Final'].isin(canal_sel))
    ]
    f_inv = df_inv
    
    if mes_sel != "Todo el Histórico":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    # --- KPI HEADER ---
    st.title(f"🚀 Dashboard Estratégico: {mes_sel}")
    
    leads_totales = len(f_leads)
    clientes_totales = len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
    pruebas_totales = len(f_leads[f_leads['Vino a prueba'] == 'Si'])
    tc_final = (clientes_totales / leads_totales * 100) if leads_totales > 0 else 0
    t_prueba = (pruebas_totales / leads_totales * 100) if leads_totales > 0 else 0
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Leads", f"{leads_totales:,}")
    m2.metric("Vino a Prueba", f"{pruebas_totales}", f"{t_prueba:.1f}%")
    m3.metric("Clientes", f"{clientes_totales}")
    m4.metric("TC (Lead a Clie)", f"{tc_final:.1f}%")
    m5.metric("Inversión Total", f"{f_inv['INVERSIÓN TOTAL'].sum():,.0f} €")

    st.markdown("---")

    # --- PESTAÑAS ---
    tab_funnel, tab_canales, tab_perdidas, tab_centros = st.tabs(["🌪️ Embudo de Ventas", "📊 Análisis Canales", "❌ Análisis de Pérdidas", "🏢 Desempeño Centros"])

    # 1. EMBUDO DE VENTAS
    with tab_funnel:
        st.subheader("Visualización del Embudo (Funnel)")
        fig_funnel = go.Figure(go.Funnel(
            y = ["Leads", "Vino a Prueba", "Clientes Captados"],
            x = [leads_totales, pruebas_totales, clientes_totales],
            textinfo = "value+percent initial",
            marker = {"color": ["#636EFA", "#EF553B", "#00CC96"]}
        ))
        st.plotly_chart(fig_funnel, use_container_width=True)
        
        st.write("### ¿Cómo nos contactan?")
        fig_forma = px.pie(f_leads, names='Forma contacto', hole=0.4, title="Distribución por Forma de Contacto")
        st.plotly_chart(fig_forma, use_container_width=True)

    # 2. ANÁLISIS POR CANAL
    with tab_canales:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.write("### Atribución: Cómo nos conocen")
            fig_conoce = px.bar(f_leads['Como conoce'].value_counts().head(10).reset_index(), x='count', y='Como conoce', orientation='h')
            st.plotly_chart(fig_conoce, use_container_width=True)
        with col_c2:
            st.write("### Rendimiento por Canal")
            resumen_canal = f_leads.groupby('Canal_Final').size().reset_index(name='Leads')
            fig_canal = px.pie(resumen_canal, values='Leads', names='Canal_Final', color='Canal_Final')
            st.plotly_chart(fig_canal, use_container_width=True)

    # 3. ANÁLISIS DE PÉRDIDAS
    with tab_perdidas:
        st.subheader("¿Por qué no cerramos las ventas?")
        df_perdidos = f_leads[f_leads['Situacion actual'].isin(['CLIENTE PERDIDO', 'LEAD NO VALIDO'])]
        causas = df_perdidos['Causa perdido'].value_counts().reset_index()
        fig_causas = px.bar(causas.head(15), x='count', y='Causa perdido', orientation='h', color='count', 
                            color_continuous_scale='Reds', title="Motivos Principales de Pérdida")
        st.plotly_chart(fig_causas, use_container_width=True)

    # 4. DESEMPEÑO POR CENTRO
    with tab_centros:
        st.subheader("Ranking de Centros")
        centro_stats = f_leads.groupby('Centro origen').agg({
            'Identificador': 'count',
            'Valor total': 'sum'
        }).rename(columns={'Identificador': 'Leads', 'Valor total': 'Ventas €'}).reset_index()
        
        fig_ranking = px.bar(centro_stats.sort_values('Leads', ascending=False), x='Centro origen', y='Leads', 
                             color='Ventas €', text_auto=True, title="Leads y Ventas por Ubicación")
        st.plotly_chart(fig_ranking, use_container_width=True)

except Exception as e:
    st.error(f"Hubo un problema al procesar los datos: {e}")
