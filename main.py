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
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

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

    f_leads = df_leads[(df_leads['Centro origen'].isin(sedes_sel)) & (df_leads['Canal_Final'].isin(canal_sel))].copy()
    f_inv = df_inv
    if mes_sel != "Histórico":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    st.title("🚀 Business Intelligence - Mundo Estudiante")
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(["🌪️ ROI Global", "🚫 No Válidos", "📉 Perdidos", "🏢 Sedes", "📞 Contacto", "🙋 Atribución", "📈 Tendencias"])

    with t1:
        st.header("Análisis de Rentabilidad")
        ing_t, inv_t = f_leads['Valor total'].sum(), f_inv['INVERSIÓN TOTAL'].sum()
        l_cap = len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos", f"{ing_t:,.0f}€")
        c2.metric("Inversión", f"{inv_t:,.0f}€")
        c3.metric("ROAS", f"{(ing_t/inv_t if inv_t>0 else 0):.2f}x")
        c4.metric("CAC", f"{(inv_t/l_cap if l_cap>0 else 0):.2f}€")
        st.plotly_chart(go.Figure(go.Funnel(y=["Leads", "Pruebas", "Ventas"], x=[len(f_leads), len(f_leads[f_leads['Vino a prueba'] == 'Si']), l_cap])), use_container_width=True)
        st.subheader("Ingresos por Canal")
        st.plotly_chart(px.bar(f_leads.groupby('Canal_Final')['Valor total'].sum().reset_index(), x='Canal_Final', y='Valor total', color='Canal_Final'), use_container_width=True)

    with t2:
        st.header("Auditoría de Calidad")
        df_nv = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO']
        st.plotly_chart(px.pie(df_nv, names='Canal_Final', title="Inválidos por Canal"), use_container_width=True)
        st.plotly_chart(px.bar(df_nv['Causa perdido'].value_counts().reset_index(), x='count', y='Causa perdido', orientation='h', title="Causas de Descarte"), use_container_width=True)

    with t3:
        st.header("Ventas Perdidas")
        df_per = f_leads[f_leads['Situacion actual'] == 'CLIENTE PERDIDO']
        st.error(f"Fuga Total: {df_per['Valor total'].sum():,.0f}€")
        st.plotly_chart(px.bar(df_per['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h'), use_container_width=True)

    with t4:
        st.header("Ranking de Sedes")
        sede_stats = f_leads.groupby('Centro origen').agg({'Identificador':'count', 'Valor total':'sum', 'Vino a prueba': lambda x: (x=='Si').sum(), 'Situacion actual': lambda x: (x=='CLIENTE CAPTADO').sum()}).reset_index()
        sede_stats.columns = ['Sede', 'Leads', 'Ventas', 'Pruebas', 'Captados']
        st.dataframe(sede_stats.sort_values('Ventas', ascending=False), use_container_width=True)
        st.plotly_chart(px.bar(sede_stats, x='Sede', y='Ventas', color='Leads', text_auto=True, title="Ventas por Sede"), use_container_width=True)

    with t5:
        st.header("Formas de Contacto")
        df_sun = f_leads.dropna(subset=['Forma contacto', 'Situacion actual'])
        st.plotly_chart(px.sunburst(df_sun, path=['Forma contacto', 'Situacion actual'], values='Valor total'), use_container_width=True)
        st.plotly_chart(px.histogram(f_leads, x='Forma contacto', color='Situacion actual', barmode='group'), use_container_width=True)

    with t6:
        st.header("Atribución Detallada")
        st.plotly_chart(px.pie(f_leads, names='Como conoce', hole=0.4), use_container_width=True)
        st.write("### Top URLs por Facturación")
        st.table(f_leads.groupby('URL')['Valor total'].sum().sort_values(ascending=False).head(15))

    with t7:
        st.header("Tendencias")
        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        st.plotly_chart(px.bar(f_leads['DIA_SEMANA'].value_counts().reindex(dias_orden).reset_index(), x='DIA_SEMANA', y='count', title="Leads por Día"), use_container_width=True)
        evol = f_leads.groupby('MES_AÑO').agg({'Identificador':'count', 'Valor total':'sum'}).reset_index()
        st.plotly_chart(px.line(evol, x='MES_AÑO', y='Valor total', title="Evolución Ingresos", markers=True), use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
