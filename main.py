import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="ME - Ultra BI Suite", layout="wide", initial_sidebar_state="expanded")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    try:
        leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
        inv = pd.read_excel(FILE, sheet_name='Inversion')
    except:
        leads = pd.read_csv('Datos_Estaticos_ME_V1__Canvas.xlsx - Total_Datos_ME.csv')
        inv = pd.read_csv('Datos_Estaticos_ME_V1__Canvas.xlsx - Inversion.csv')
    
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    leads['DIA_SEMANA'] = leads['PERIODO'].dt.day_name()
    leads['HORA'] = leads['PERIODO'].dt.hour # Si tienes la hora en el Excel
    
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

    # Lógica de Canales
    leads['Canal_Final'] = 'Otros / Orgánico'
    leads.loc[(leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False)), 'Canal_Final'] = 'Google Ads'
    leads.loc[(leads['URL'].str.contains('meta|facebook|instagram', case=False, na=False)) | (leads['Telekos'].str.contains('facebook', case=False, na=False)), 'Canal_Final'] = 'Meta Ads'
    leads.loc[(leads['GCLID'].isnull()) & (~leads['URL'].str.contains('meta|tiktok|gads', case=False, na=False)) & (leads['SEM / SEO'] == 'SEO'), 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    with st.sidebar:
        st.header("🎮 Centro de Control")
        mes_sel = st.selectbox("📅 Periodo", ["Histórico"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True))
        sedes_sel = st.multiselect("📍 Sedes", df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Canales", df_leads['Canal_Final'].unique(), default=df_leads['Canal_Final'].unique())

    # Filtrado
    f_leads = df_leads[(df_leads['Centro origen'].isin(sedes_sel)) & (df_leads['Canal_Final'].isin(canal_sel))].copy()
    f_inv = df_inv
    if mes_sel != "Histórico":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    st.title(f"🚀 Business Intelligence - Mundo Estudiante")
    st.markdown(f"**Analizando:** {mes_sel} | {', '.join(sedes_sel[:2])}... | {len(f_leads)} Leads")

    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "🌪️ ROI Global", "🚫 No Válidos", "📉 Perdidos", "🏢 Sedes", "📞 Contacto", "🙋 Atribución", "📈 Tendencias"
    ])

    # --- PESTAÑA 1: ROI Y FUNNEL ---
    with t1:
        st.header("Análisis de Rentabilidad (ROI)")
        ing_t, inv_t = f_leads['Valor total'].sum(), f_inv['INVERSIÓN TOTAL'].sum()
        l_cap = len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos Reales", f"{ing_t:,.0f}€")
        c2.metric("Inversión Ads", f"{inv_t:,.0f}€")
        c3.metric("ROAS", f"{(ing_t/inv_t if inv_t>0 else 0):.2f}x")
        c4.metric("Coste Adquisición (CAC)", f"{(inv_t/l_cap if l_cap>0 else 0):.2f}€")

        st.markdown("---")
        st.subheader("Embudo de Conversión Detallado")
        fig_f = go.Figure(go.Funnel(
            y=["Leads", "Pruebas", "Ventas"], 
            x=[len(f_leads), len(f_leads[f_leads['Vino a prueba'] == 'Si']), l_cap],
            textinfo="value+percent initial"))
        st.plotly_chart(fig_f, use_container_width=True)

        st.subheader("💰 Distribución de Ingresos por Canal")
        fig_rev = px.bar(f_leads.groupby('Canal_Final')['Valor total'].sum().reset_index(), 
                         x='Canal_Final', y='Valor total', color='Canal_Final', text_auto='.2s')
        st.plotly_chart(fig_rev, use_container_width=True)

    # --- PESTAÑA 2: NO VÁLIDOS ---
    with t2:
        st.header("Auditoría de Calidad")
        df_nv = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO']
        
        col_nv1, col_nv2 = st.columns(2)
        with col_nv1:
            st.plotly_chart(px.pie(df_nv, names='Canal_Final', title="Inválidos por Canal"), use_container_width=True)
        with col_nv2:
            st.plotly_chart(px.bar(df_nv['Centro origen'].value_counts().reset_index(), x='count', y='Centro origen', orientation='h', title="Inválidos por Sede"), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Razones de Descarte (Lead No Válido)")
        fig_cause = px.treemap(df_nv, path=['Causa perdido', 'Canal_Final'], title="Mapa de Causas y Origen")
        st.plotly_chart(fig_cause, use_container_width=True)

    # --- PESTAÑA 3: PERDIDOS ---
    with t3:
        st.header("Análisis de Ventas Perdidas")
        df_per = f_leads[f_leads['Situacion actual'] == 'CLIENTE PERDIDO']
        st.error(f"Fuga Total de Ingresos: {df_per['Valor total'].sum():,.0f}€")
        
        st.plotly_chart(px.bar(df_per['Causa perdido'].value_counts().head(10).reset_index(), 
                               x='count', y='Causa perdido', orientation='h', color='count'), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Pérdida por Canal de Captación")
        fig_per_can = px.box(df_per, x='Canal_Final', y='Valor total', points="all", title="Dispersión del Valor Perdido por Canal")
        st.plotly_chart(fig_per_can, use_container_width=True)

    # --- PESTAÑA 4: SEDES ---
    with t4:
        st.header("Ranking y Comparativa de Sedes")
        sede_stats = f_leads.groupby('Centro origen').agg({
            'Identificador': 'count', 
            'Valor total': 'sum', 
            'Vino a prueba': lambda x: (x=='Si').sum(),
            'Situacion actual': lambda x: (x=='CLIENTE CAPTADO').sum()
        }).reset_index()
        sede_stats.columns = ['Sede', 'Leads', 'Ventas', 'Pruebas', 'Captados']
        sede_stats['Ratio_Venta'] = (sede_stats['Captados'] / sede_stats['Leads'] * 100).round(1)

        st.dataframe(sede_stats.sort_values('Ventas', ascending=False), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Eficiencia de Cierre por Sede (%)")
        st.plotly_chart(px.bar(sede_stats
