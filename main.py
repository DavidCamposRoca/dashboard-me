import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Mundo Estudiante - Master BI", layout="wide")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
    inv = pd.read_excel(FILE, sheet_name='Inversion')
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

    # Lógica de Atribución de Canales
    leads['Canal_Final'] = 'Otros'
    leads.loc[(leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False)), 'Canal_Final'] = 'Google Ads'
    leads.loc[(leads['URL'].str.contains('meta|facebook', case=False, na=False)) | (leads['Telekos'].str.contains('facebook', case=False, na=False)), 'Canal_Final'] = 'Meta Ads'
    leads.loc[(leads['GCLID'].isnull()) & (~leads['URL'].str.contains('meta|tiktok|gads', case=False, na=False)) & (leads['SEM / SEO'] == 'SEO'), 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- CENTRO DE CONTROL (SIDEBAR) ---
    with st.sidebar:
        st.title("🕹️ Centro de Control")
        mes_sel = st.selectbox("📅 Periodo", ["Histórico"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True))
        sedes_sel = st.multiselect("📍 Sedes", df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Canal", ['Google Ads', 'Meta Ads', 'SEO', 'Otros'], default=['Google Ads', 'Meta Ads', 'SEO', 'Otros'])

    # Filtrado Global
    f_leads = df_leads[(df_leads['Centro origen'].isin(sedes_sel)) & (df_leads['Canal_Final'].isin(canal_sel))]
    f_inv = df_inv
    if mes_sel != "Histórico":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    st.title(f"📊 Dashboard de Rendimiento: {mes_sel}")

    # --- DEFINICIÓN DE PESTAÑAS ---
    t1, t2, t3, t4, t5, t6 = st.tabs([
        "🌪️ Embudo y ROI", "🚫 No Válidos", "📉 Perdidos", "🏢 Sedes", "📞 Contacto", "🙋 Atribución"
    ])

    # PESTAÑA 1: EMBUDO Y ROI
    with t1:
        st.header("Embudo de Ventas y Rentabilidad")
        l_tot = len(f_leads)
        l_pru = len(f_leads[f_leads['Vino a prueba'] == 'Si'])
        l_cap = len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
        inversion = f_inv['INVERSIÓN TOTAL'].sum()
        ingresos = f_leads['Valor total'].sum()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Leads", f"{l_tot}")
        m2.metric("A Prueba", f"{l_pru}", f"{(l_pru/l_tot*100 if l_tot>0 else 0):.1f}%")
        m3.metric("Clientes", f"{l_cap}", f"{(l_cap/l_tot*100 if l_tot>0 else 0):.1f}%")
        m4.metric("Inversión", f"{inversion:,.0f}€")
        m5.metric("ROAS", f"{(ingresos/inversion if inversion>0 else 0):.2f}x")

        fig_fun = go.Figure(go.Funnel(y=["Leads", "Pruebas", "Clientes"], x=[l_tot, l_pru, l_cap]))
        st.plotly_chart(fig_fun, use_container_width=True)

    # PESTAÑA 2: NO VÁLIDOS
    with t2:
        st.header("Análisis de Leads No Válidos")
        df_nv = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO']
        st.metric("Total No Válidos", len(df_nv), f"{(len(df_nv)/l_tot*100 if l_tot>0 else 0):.1f}%", delta_color="inverse")
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.pie(df_nv, names='Canal_Final', title="No Válidos por Canal"), use_container_width=True)
        c2.plotly_chart(px.bar(df_nv['Causa perdido'].value_counts().reset_index(), x='count', y='Causa perdido', orientation='h', title="Motivos de Descarte"), use_container_width=True)

    # PESTAÑA 3: PERDIDOS
    with t3:
        st.header("Análisis de Clientes Perdidos")
        df_per = f_leads[f_leads['Situacion actual'] == 'CLIENTE PERDIDO']
        st.plotly_chart(px.bar(df_per['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h', title="Top Motivos de Pérdida"), use_container_width=True)
        st.write("### Detalle de Perdidos")
        st.dataframe(df_per[['Identificador', 'Centro origen', 'Canal_Final', 'Causa perdido', 'Valor total']].head(50))

    # PESTAÑA 4: SEDES
    with t4:
        st.header("Rendimiento por Sede")
        sede_data = f_leads.groupby('Centro origen').agg({'Identificador':'count', 'Valor total':'sum'}).reset_index()
        sede_data.columns = ['Sede', 'Leads', 'Ventas']
        st.plotly_chart(px.bar(sede_data, x='Sede', y='Leads', color='Ventas', text_auto=True, title="Leads y Ventas por Sede"), use_container_width=True)

    # PESTAÑA 5: FORMAS DE CONTACTO
    with t5:
        st.header("Efectividad de Formas de Contacto")
        st.plotly_chart(px.pie(f_leads, names='Forma contacto', title="¿Por dónde nos escriben?"), use_container_width=True)
        st.plotly_chart(px.bar(f_leads, x='Forma contacto', color='Situacion actual', title="Conversión según Forma de Contacto"), use_container_width=True)

    # PESTAÑA 6: ATRIBUCIÓN (CÓMO NOS CONOCE)
    with t6:
        st.header("Atribución: Cómo nos conocen")
        fig_at = px.treemap(f_leads, path=['Como conoce', 'Canal_Final'], title="Jerarquía de Atribución")
        st.plotly_chart(fig_at, use_container_width=True)
        st.write("### Tabla de Origen")
        st.dataframe(f_leads['Como conoce'].value_counts())

except Exception as e:
    st.error(f"Error: {e}")
