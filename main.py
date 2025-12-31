import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Mundo Estudiante - Master BI", layout="wide", initial_sidebar_state="expanded")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    # Nota: Si en tu GitHub el archivo sigue siendo .xlsx, usamos read_excel
    leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
    inv = pd.read_excel(FILE, sheet_name='Inversion')
    
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

    # LÓGICA DE CANALES
    leads['Canal_Final'] = 'Otros'
    mask_gads = (leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False))
    leads.loc[mask_gads, 'Canal_Final'] = 'Google Ads'
    
    mask_meta = (leads['URL'].str.contains('meta|facebook', case=False, na=False)) | \
                (leads['Telekos'].str.contains('facebook', case=False, na=False))
    leads.loc[mask_meta, 'Canal_Final'] = 'Meta Ads'
    
    mask_seo = (leads['GCLID'].isnull()) & \
               (~leads['URL'].str.contains('meta|tiktok|gads|gad_|gbraid|wbraid', case=False, na=False)) & \
               (leads['SEM / SEO'] == 'SEO')
    leads.loc[mask_seo, 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- SELECTORES LATERALES ---
    with st.sidebar:
        st.image("https://www.mundoestudiante.com/wp-content/uploads/2020/09/logo-mundo-estudiante.png", width=200)
        st.title("Centro de Control")
        mes_sel = st.selectbox("📅 Periodo Temporal", ["Todo el Histórico"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True))
        centro_sel = st.multiselect("📍 Centros", options=df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Canal de Captación", options=['Google Ads', 'Meta Ads', 'SEO', 'Otros'], default=['Google Ads', 'Meta Ads', 'SEO', 'Otros'])

    # --- FILTRADO ---
    f_leads = df_leads[(df_leads['Centro origen'].isin(centro_sel)) & (df_leads['Canal_Final'].isin(canal_sel))]
    f_inv = df_inv
    if mes_sel != "Todo el Histórico":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    st.title(f"🚀 Business Intelligence: {mes_sel}")
    
    # --- PESTAÑAS ---
    tab_gen, tab_gads, tab_meta, tab_seo, tab_invalid = st.tabs([
        "📊 Global", "🔍 Google Ads", "📱 Meta Ads", "📈 SEO", "❌ Leads No Válidos"
    ])

    # Función para métricas comunes (Reutilizable)
    def render_common_metrics(df, inversion, titulo):
        l_tot = len(df)
        l_cap = len(df[df['Situacion actual'] == 'CLIENTE CAPTADO'])
        l_inv = len(df[df['Situacion actual'] == 'LEAD NO VALIDO'])
        val = df['Valor total'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Leads", f"{l_tot}")
        c2.metric("Captados", f"{l_cap}")
        c3.metric("Inválidos", f"{l_inv}", f"{(l_inv
