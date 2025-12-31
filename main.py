import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="ME - Intelligence Suite PRO", layout="wide")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    try:
        leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
        inv = pd.read_excel(FILE, sheet_name='Inversion')
    except:
        leads = pd.read_csv('Datos_Estaticos_ME_V1__Canvas.xlsx - Total_Datos_ME.csv')
        inv = pd.read_csv('Datos_Estaticos_ME_V1__Canvas.xlsx - Inversion.csv')
    
    # Limpieza de fechas y creación de nuevas dimensiones
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    leads['DIA_SEMANA'] = leads['PERIODO'].dt.day_name()
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
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

    # --- PESTAÑAS ---
    t1, t2, t3, t4, t5, t6, t7 = st.tabs([
        "🌪️ ROI Global", "🚫 No Válidos", "📉 Perdidos", "🏢 Sedes", "📞 Contacto", "🙋 Atribución", "📈 Tendencias"
    ])

    # PESTAÑA 7: TENDENCIAS (NUEVA)
    with t7:
        st.header("Análisis de Temporalidad y Comportamiento")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.write("### Leads por Día de la Semana")
            dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            fig_dias = px.bar(f_leads['DIA_SEMANA'].value_counts().reindex(dias_orden).reset_index(), 
                             x='DIA_SEMANA', y='count', title="¿Cuándo entran más leads?", color_discrete_sequence=['#636EFA'])
            st.plotly_chart(fig_dias, use_container_width=True)
        with col_t2:
            st.write("### Evolución Mensual de Ventas (€)")
            evol_ventas = f_leads.groupby('MES_AÑO')['Valor total'].sum().reset_index()
            fig_evol = px.line(evol_ventas, x='MES_AÑO', y='Valor total', markers=True, title="Facturación en el tiempo")
            st.plotly_chart(fig_evol, use_container_width=True)

    # Mejoramos PESTAÑA 4: SEDES (Añadimos tasa de éxito de prueba)
    with t4:
        st.header("Rendimiento Detallado por Sede")
        sede_stats = f_leads.groupby('Centro origen').agg({
            'Identificador': 'count',
            'Vino a prueba': lambda x: (x=='Si').sum(),
            'Situacion actual': lambda x: (x=='CLIENTE CAPTADO').sum(),
            'Valor total': 'sum'
        }).reset_index()
        sede_stats.columns = ['Sede', 'Leads', 'Pruebas', 'Captados', 'Ingresos']
        sede_stats['% Éxito Prueba'] = (sede_stats['Captados'] / sede_stats['Pruebas'] * 100).round(1)
        
        st.dataframe(sede_stats.sort_values('Ingresos', ascending=False), use_container_width=True)
        st.write("### Tasa de éxito: De Prueba a Cliente")
        st.plotly_chart(px.bar(sede_stats, x='Sede', y='% Éxito Prueba', color='% Éxito Prueba', text_auto=True), use_container_width=True)

    # (El resto de pestañas se mantienen con el código robusto anterior)
    # ... [Aquí se incluyen las lógicas de T1, T2, T3, T5, T6 del mensaje anterior] ...
    # Nota: Por brevedad no repito todo el código de las otras pestañas, 
    # pero el usuario debe mantenerlas.

except Exception as e:
    st.error(f"Error: {e}")
