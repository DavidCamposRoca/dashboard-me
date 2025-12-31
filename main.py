import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página con tema ancho
st.set_page_config(page_title="Mundo Estudiante - Master BI", layout="wide", initial_sidebar_state="expanded")

# Nombre exacto del archivo que subiste a GitHub
FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    # Cargamos las dos hojas del Excel
    leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
    inv = pd.read_excel(FILE, sheet_name='Inversion')
    
    # Formateo de fechas
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

    # --- LÓGICA DE SEGMENTACIÓN ---
    leads['Canal_Final'] = 'Otros'
    
    # Google Ads: GCLID existe o marca SEM
    mask_gads = (leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False))
    leads.loc[mask_gads, 'Canal_Final'] = 'Google Ads'
    
    # Meta (FB/IG): META en URL o facebook en Telekos
    mask_meta = (leads['URL'].str.contains('meta|facebook', case=False, na=False)) | \
                (leads['Telekos'].str.contains('facebook', case=False, na=False))
    leads.loc[mask_meta, 'Canal_Final'] = 'Meta Ads'
    
    # SEO: Sin GCLID, sin marcas de ads en URL y marcado como SEO en columna
    mask_seo = (leads['GCLID'].isnull()) & \
               (~leads['URL'].str.contains('meta|tiktok|gads|gad_|gbraid|wbraid', case=False, na=False)) & \
               (leads['SEM / SEO'] == 'SEO')
    leads.loc[mask_seo, 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- BARRA LATERAL (SELECTORES) ---
    with st.sidebar:
        st.title("Centro de Control")
        meses = ["Todo el Histórico"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True)
        mes_sel = st.selectbox("📅 Periodo Temporal", meses)
        centro_sel = st.multiselect("📍 Centros", options=df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Canal de Captación", options=['Google Ads', 'Meta Ads', 'SEO', 'Otros'], default=['Google Ads', 'Meta Ads', 'SEO', 'Otros'])

    # --- FILTRADO DE DATOS ---
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

    # Función interna para renderizar métricas sin errores de sintaxis
    def render_metrics(df_filtrado, inversion_total):
        l_tot = len(df_filtrado)
        l_cap = len(df_filtrado[df_filtrado['Situacion actual'] == 'CLIENTE CAPTADO'])
        l_inv = len(df_filtrado[df_filtrado['Situacion actual'] == 'LEAD NO VALIDO'])
        l_pru = len(df_filtrado[df_filtrado['Vino a prueba'] == 'Si'])
        val_t = df_filtrado['Valor total'].sum()
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Leads", f"{l_tot:,}")
        
        # Cálculos de porcentajes seguros
        p_pru = (l_pru / l_tot * 100) if l_tot > 0 else 0
        p_cap = (l_cap / l_tot * 100) if l_tot > 0 else 0
        p_inv = (l_inv / l_tot * 100) if l_tot > 0 else 0
        
        c2.metric("A Prueba", f"{l_pru}", f"{p_pru:.1f}%")
        c3.metric("Captados", f"{l_cap}", f"{p_cap:.1f}%")
        c4.metric("Inválidos", f"{l_inv}", f"{p_inv:.1f}%", delta_color="inverse")
        c5.metric("Valor Total", f"{val_t:,.0f} €")

    # --- CONTENIDO DE PESTAÑAS ---
    with tab_gen:
        inv_gen = f_inv['INVERSIÓN TOTAL'].sum()
        render_metrics(f_leads, inv_gen)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(f_leads, names='Situacion actual', title="Estados de los Leads", hole=0.4), use_container_width=True)
        with col2:
            st.plotly_chart(px.bar(f_leads['Canal_Final'].value_counts().reset_index(), x='Canal_Final', y='count', title="Distribución por Canal"), use_container_width=True)

    with tab_gads:
        df_g = f_leads[f_leads['Canal_Final'] == 'Google Ads']
        inv_g = f_inv['INVERSIÓN EN G ADS'].sum()
        render_metrics(df_g, inv_g)
        if inv_g > 0 and len(df_g) > 0:
            st.info(f"💰 CPL: {(inv_g/len(df_g)):.2f}€  |  ROAS: {(df_g['Valor total'].sum()/inv_g):.2f}x")

    with tab_meta:
        df_m = f_leads[f_leads['Canal_Final'] == 'Meta Ads']
        inv_m = f_inv['INVERSIÓN EN META'].sum()
        render_metrics(df_m, inv_m)

    with tab_seo:
        df_s = f_leads[f_leads['Canal_Final'] == 'SEO']
        st.subheader("Tráfico Orgánico")
        render_metrics(df_s, 0)
        st.write("### URLs con más leads SEO")
        st.dataframe(df_s['URL'].value_counts().head(10))

    with tab_invalid:
        st.header("Análisis de Leads No Válidos")
        df_no_val = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO']
        if not df_no_val.empty:
            c_inv1, c_inv2 = st.columns(2)
            with c_inv1:
                st.plotly_chart(px.pie(df_no_val, names='Canal_Final', title="Inválidos por Canal"), use_container_width=True)
            with c_inv2:
                st.plotly_chart(px.bar(df_no_val['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h', title="Motivos de Invalidez"), use_container_width=True)
        else:
            st.success("No hay leads no válidos en este filtro.")

except Exception as e:
    st.error(f"Error al cargar datos: {e}")
