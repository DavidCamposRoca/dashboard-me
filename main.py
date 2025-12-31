import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración profesional
st.set_page_config(page_title="Mundo Estudiante - Business Intelligence", layout="wide")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    try:
        leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
        inv = pd.read_excel(FILE, sheet_name='Inversion')
    except:
        leads = pd.read_csv('Datos_Estaticos_ME_V1__Canvas.xlsx - Total_Datos_ME.csv')
        inv = pd.read_csv('Datos_Estaticos_ME_V1__Canvas.xlsx - Inversion.csv')
    
    # Procesamiento de Fechas
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    leads['DIA_SEMANA'] = leads['PERIODO'].dt.day_name()
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

    # Lógica de Canales (Atribución)
    leads['Canal_Final'] = 'Otros / Orgánico'
    leads.loc[(leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False)), 'Canal_Final'] = 'Google Ads'
    leads.loc[(leads['URL'].str.contains('meta|facebook|instagram', case=False, na=False)) | (leads['Telekos'].str.contains('facebook', case=False, na=False)), 'Canal_Final'] = 'Meta Ads'
    leads.loc[(leads['GCLID'].isnull()) & (~leads['URL'].str.contains('meta|tiktok|gads', case=False, na=False)) & (leads['SEM / SEO'] == 'SEO'), 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- CENTRO DE CONTROL (SIDEBAR) ---
    with st.sidebar:
        st.header("🎮 Centro de Control")
        mes_sel = st.selectbox("📅 Periodo", ["Histórico"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True))
        sedes_sel = st.multiselect("📍 Sedes", df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Canales", df_leads['Canal_Final'].unique(), default=df_leads['Canal_Final'].unique())

    # Filtros Dinámicos
    f_leads = df_leads[(df_leads['Centro origen'].isin(sedes_sel)) & (df_leads['Canal_Final'].isin(canal_sel))].copy()
    f_inv = df_inv
    if mes_sel != "Histórico":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    # --- MÉTRICAS GENERALES ---
    l_tot, l_pru, l_cap = len(f_leads), len(f_leads[f_leads['Vino a prueba'] == 'Si']), len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
    ing_t, inv_t = f_leads['Valor total'].sum(), f_inv['INVERSIÓN TOTAL'].sum()

    st.title(f"📈 Inteligencia de Negocio: {mes_sel}")

    # --- PESTAÑAS ---
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "🌪️ ROI Global", "🚫 No Válidos", "📉 Perdidos", "🏢 Sedes", "📞 Contacto", "🙋 Atribución", "📈 Tendencias"
    ])

    # T1: ROI Y FUNNEL
    with t1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos", f"{ing_t:,.0f}€")
        c2.metric("Inversión", f"{inv_t:,.0f}€")
        c3.metric("ROAS", f"{(ing_t/inv_t if inv_t>0 else 0):.2f}x")
        c4.metric("CPL Medio", f"{(inv_t/l_tot if l_tot>0 else 0):.2f}€")
        
        fig_fun = go.Figure(go.Funnel(y=["Leads", "Pruebas", "Ventas"], x=[l_tot, l_pru, l_cap], textinfo="value+percent initial"))
        st.plotly_chart(fig_fun, use_container_width=True)

    # T2: NO VÁLIDOS
    with t2:
        df_nv = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO']
        st.subheader(f"Análisis de leads descartados ({len(df_nv)})")
        col_nv1, col_nv2 = st.columns(2)
        with col_nv1:
            st.plotly_chart(px.pie(df_nv, names='Canal_Final', title="Descartes por Canal"), use_container_width=True)
        with col_nv2:
            st.plotly_chart(px.bar(df_nv['Causa perdido'].value_counts().reset_index(), x='count', y='Causa perdido', orientation='h', title="Motivos Técnicos"), use_container_width=True)

    # T3: PERDIDOS
    with t3:
        df_per = f_leads[f_leads['Situacion actual'] == 'CLIENTE PERDIDO']
        st.error(f"Ventas No Cerradas (Potencial): {df_per['Valor total'].sum():,.0f}€")
        st.plotly_chart(px.bar(df_per['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h', title="Motivos de Pérdida Comercial"), use_container_width=True)

    # T4: SEDES
    with t4:
        st.subheader("Rendimiento por Academia")
        sede_stats = f_leads.groupby('Centro origen').agg({'Identificador':'count', 'Valor total':'sum', 'Vino a prueba': lambda x: (x=='Si').sum()}).reset_index()
        sede_stats.columns = ['Sede', 'Leads', 'Ventas', 'Pruebas']
        st.plotly_chart(px.bar(sede_stats, x='Sede', y='Leads', color='Ventas', text_auto=True, title="Captación y Facturación"), use_container_width=True)
        st.write("### Tabla Detallada")
        st.dataframe(sede_stats, use_container_width=True)

    # T5: CONTACTO
    with t5:
        st.subheader("Análisis de Formas de Contacto")
        df_c = f_leads.dropna(subset=['Forma contacto'])
        st.plotly_chart(px.pie(df_c, names='Forma contacto', title="¿Cómo llegan los leads?"), use_container_width=True)
        st.plotly_chart(px.box(f_leads, x="Forma contacto", y="Valor total", title="Valor del Lead según Canal"), use_container_width=True)

    # T6: ATRIBUCIÓN
    with t6:
        st.subheader("¿Cómo nos conocen?")
        st.plotly_chart(px.pie(f_leads, names='Como conoce', hole=0.3), use_container_width=True)
        st.write("### Top URLs por Ingresos")
        st.table(f_leads.groupby('URL')['Valor total'].sum().sort_values(ascending=False).head(10))

    # T7: TENDENCIAS
    with t7:
        st.subheader("Patrones Temporales")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            fig_d = px.bar(f_leads['DIA_SEMANA'].value_counts().reindex(dias_orden).reset_index(), x='DIA_SEMANA', y='count', title="Leads por Día de la Semana")
            st.plotly_chart(fig_d, use_container_width=True)
        with col_t2:
            evol_v = f_leads.groupby('MES_AÑO')['Valor total'].sum().reset_index()
            st.plotly_chart(px.line(evol_v, x='MES_AÑO', y='Valor total', title="Evolución Mensual de Ingresos", markers=True), use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
