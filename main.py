import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="BI Mundo Estudiante - Pro", layout="wide")

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
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

    # Atribución de Canales
    leads['Canal_Final'] = 'Otros / Orgánico'
    leads.loc[(leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False)), 'Canal_Final'] = 'Google Ads'
    leads.loc[(leads['URL'].str.contains('meta|facebook|instagram', case=False, na=False)) | (leads['Telekos'].str.contains('facebook', case=False, na=False)), 'Canal_Final'] = 'Meta Ads'
    leads.loc[(leads['GCLID'].isnull()) & (~leads['URL'].str.contains('meta|tiktok|gads', case=False, na=False)) & (leads['SEM / SEO'] == 'SEO'), 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    with st.sidebar:
        st.title("🕹️ Intelligence Control")
        mes_sel = st.selectbox("📅 Seleccionar Periodo", ["Histórico Completo"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True))
        sedes_sel = st.multiselect("📍 Filtrar por Sedes", df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Filtrar por Canales", df_leads['Canal_Final'].unique(), default=df_leads['Canal_Final'].unique())

    # FILTRADO
    f_leads = df_leads[(df_leads['Centro origen'].isin(sedes_sel)) & (df_leads['Canal_Final'].isin(canal_sel))].copy()
    f_inv = df_inv
    if mes_sel != "Histórico Completo":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    st.title(f"📈 Análisis de Negocio: {mes_sel}")

    t1, t2, t3, t4, t5, t6 = st.tabs(["🌪️ ROI y Funnel", "🚫 Calidad", "📉 Perdidos", "🏢 Sedes", "📞 Contacto", "🙋 Atribución"])

    with t1:
        st.subheader("Rendimiento Económico")
        l_tot, l_pru, l_cap = len(f_leads), len(f_leads[f_leads['Vino a prueba'] == 'Si']), len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
        inv_t, ing_t = f_inv['INVERSIÓN TOTAL'].sum(), f_leads['Valor total'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos", f"{ing_t:,.0f}€")
        c2.metric("Inversión", f"{inv_t:,.0f}€")
        c3.metric("ROAS", f"{(ing_t/inv_t if inv_t>0 else 0):.2f}x")
        c4.metric("CAC", f"{(inv_t/l_cap if l_cap>0 else 0):.2f}€")

        fig_fun = go.Figure(go.Funnel(y=["Leads", "Pruebas", "Clientes"], x=[l_tot, l_pru, l_cap]))
        st.plotly_chart(fig_fun, use_container_width=True)

    with t2:
        st.subheader("Leads No Válidos")
        df_nv = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO'].copy()
        st.metric("Tasa de Descarte", f"{(len(df_nv)/len(f_leads)*100 if len(f_leads)>0 else 0):.1f}%")
        st.plotly_chart(px.pie(df_nv, names='Canal_Final', title="Inválidos por Canal"), use_container_width=True)

    with t3:
        st.subheader("Análisis de Pérdidas")
        df_per = f_leads[f_leads['Situacion actual'] == 'CLIENTE PERDIDO'].copy()
        st.error(f"Ventas No Cerradas: {df_per['Valor total'].sum():,.0f}€")
        st.plotly_chart(px.bar(df_per['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h'), use_container_width=True)

    with t4:
        st.subheader("Rendimiento por Sede")
        sede_stats = f_leads.groupby('Centro origen').agg({'Identificador': 'count', 'Valor total': 'sum'}).reset_index()
        st.plotly_chart(px.bar(sede_stats, x='Centro origen', y='Valor total', color='Identificador', title="Facturación vs Volumen por Sede"), use_container_width=True)

    with t5:
        st.subheader("Formas de Contacto")
        # LIMPIEZA PARA EVITAR EL ERROR DE "NONE ENTRIES"
        df_sun = f_leads[['Forma contacto', 'Situacion actual', 'Valor total']].dropna(subset=['Forma contacto', 'Situacion actual'])
        if not df_sun.empty:
            fig_sun = px.sunburst(df_sun, path=['Forma contacto', 'Situacion actual'], values='Valor total')
            st.plotly_chart(fig_sun, use_container_width=True)
        else:
            st.info("No hay datos suficientes para el gráfico circular.")

    with t6:
        st.subheader("Atribución")
        st.plotly_chart(px.pie(f_leads, names='Como conoce', hole=0.3), use_container_width=True)

except Exception as e:
    st.error(f"Error en la carga de datos: {e}")
