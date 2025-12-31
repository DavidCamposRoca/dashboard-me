import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="ME - Executive BI Suite", layout="wide", initial_sidebar_state="expanded")

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

    st.title(f"🚀 Business Intelligence - Mundo Estudiante")
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(["🌪️ ROI Global", "🚫 No Válidos", "📉 Perdidos", "🏢 Sedes", "📞 Contacto", "🙋 Atribución", "📈 Tendencias"])

    # --- PESTAÑA 1: ROI Y FUNNEL ---
    with t1:
        st.header("Análisis Económico")
        ing_t, inv_t = f_leads['Valor total'].sum(), f_inv['INVERSIÓN TOTAL'].sum()
        l_cap = len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos Totales", f"{ing_t:,.0f}€")
        c2.metric("Inversión Ads", f"{inv_t:,.0f}€")
        c3.metric("ROAS", f"{(ing_t/inv_t if inv_t>0 else 0):.2f}x")
        c4.metric("CAC (Coste Adquisición)", f"{(inv_t/l_cap if l_cap>0 else 0):.2f}€")
        
        st.plotly_chart(go.Figure(go.Funnel(y=["Leads", "Pruebas", "Ventas"], x=[len(f_leads), len(f_leads[f_leads['Vino a prueba'] == 'Si']), l_cap], textinfo="value+percent initial")), use_container_width=True)
        
        st.subheader("Ingresos por Canal (€)")
        fig_ing_can = px.bar(f_leads.groupby('Canal_Final')['Valor total'].sum().reset_index(), x='Canal_Final', y='Valor total', color='Canal_Final', text_auto='.3s')
        st.plotly_chart(fig_ing_can, use_container_width=True)

    # --- PESTAÑA 2: NO VÁLIDOS ---
    with t2:
        df_nv = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO']
        st.subheader(f"Análisis de leads descartados ({len(df_nv)} leads)")
        st.plotly_chart(px.pie(df_nv, names='Canal_Final', title="Inválidos por Canal"), use_container_width=True)
        
        st.subheader("Causas de Descarte por Sede")
        fig_nv_sede = px.bar(df_nv['Centro origen'].value_counts().reset_index(), x='count', y='Centro origen', orientation='h', text_auto=True, title="Leads Inválidos por Ubicación")
        st.plotly_chart(fig_nv_sede, use_container_width=True)

    # --- PESTAÑA 3: PERDIDOS ---
    with t3:
        df_per = f_leads[f_leads['Situacion actual'] == 'CLIENTE PERDIDO']
        st.error(f"Fuga Total de Ingresos: {df_per['Valor total'].sum():,.0f}€")
        
        fig_per_causa = px.bar(df_per['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h', text_auto=True, title="Motivos Principales de Pérdida")
        st.plotly_chart(fig_per_causa, use_container_width=True)
        
        st.subheader("Valor Perdido por Canal (€)")
        fig_per_val = px.bar(df_per.groupby('Canal_Final')['Valor total'].sum().reset_index(), x='Canal_Final', y='Valor total', text_auto='.3s', color_discrete_sequence=['red'])
        st.plotly_chart(fig_per_val, use_container_width=True)

    # --- PESTAÑA 4: SEDES ---
    with t4:
        sede_stats = f_leads.groupby('Centro origen').agg({'Identificador':'count', 'Valor total':'sum', 'Situacion actual': lambda x: (x=='CLIENTE CAPTADO').sum()}).reset_index()
        sede_stats.columns = ['Sede', 'Leads', 'Ventas', 'Captados']
        sede_stats['%_Conversion'] = (sede_stats['Captados'] / sede_stats['Leads'] * 100).round(1)
        
        st.subheader("Facturación por Sede (€)")
        st.plotly_chart(px.bar(sede_stats.sort_values('Ventas', ascending=False), x='Sede', y='Ventas', text_auto='.3s', color='Ventas'), use_container_width=True)
        
        st.subheader("Eficiencia de Cierre (%)")
        st.plotly_chart(px.bar(sede_stats.sort_values('%_Conversion', ascending=False), x='Sede', y='%_Conversion', text_auto='.1f', color='%_Conversion', color_continuous_scale='Greens'), use_container_width=True)

    # --- PESTAÑA 5: CONTACTO ---
    with t5:
        st.subheader("Volumen por Forma de Contacto")
        st.plotly_chart(px.bar(f_leads['Forma contacto'].value_counts().reset_index(), x='Forma contacto', y='count', text_auto=True), use_container_width=True)
        
        st.subheader("Ingresos por Forma de Contacto (€)")
        fig_cont_val = px.bar(f_leads.groupby('Forma contacto')['Valor total'].sum().reset_index(), x='Forma contacto', y='Valor total', text_auto='.3s', color='Valor total')
        st.plotly_chart(fig_cont_val, use_container_width=True)

    # --- PESTAÑA 6: ATRIBUCIÓN ---
    with t6:
        st.subheader("Distribución de Atribución")
        st.plotly_chart(px.pie(f_leads, names='Como conoce', hole=0.4), use_container_width=True)
        
        st.subheader("Ranking de Ingresos por Origen Declarado (€)")
        fig_atr_val = px.bar(f_leads.groupby('Como conoce')['Valor total'].sum().sort_values(ascending=False).head(10).reset_index(), x='Valor total', y='Como conoce', orientation='h', text_auto='.3s')
        st.plotly_chart(fig_atr_val, use_container_width=True)

    # --- PESTAÑA 7: TENDENCIAS ---
    with t7:
        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        st.subheader("Leads por Día de la Semana")
        fig_dia = px.bar(f_leads['DIA_SEMANA'].value_counts().reindex(dias_orden).reset_index(), x='DIA_SEMANA', y='count', text_auto=True, color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig_dia, use_container_width=True)
        
        st.subheader("Evolución Facturación Mensual (€)")
        evol_v = f_leads.groupby('MES_AÑO')['Valor total'].sum().reset_index()
        st.plotly_chart(px.line(evol_v, x='MES_AÑO', y='Valor total', markers=True, text=[f"{v:,.0f}€" for v in evol_v['Valor total']]), use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
