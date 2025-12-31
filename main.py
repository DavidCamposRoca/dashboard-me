import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
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
    
    # Procesamiento de Fechas y Periodos
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    leads['DIA_SEMANA'] = leads['PERIODO'].dt.day_name()
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

    # Clasificación de Canales
    leads['Canal_Final'] = 'Otros / Orgánico'
    leads.loc[(leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False)), 'Canal_Final'] = 'Google Ads'
    leads.loc[(leads['URL'].str.contains('meta|facebook|instagram', case=False, na=False)) | (leads['Telekos'].str.contains('facebook', case=False, na=False)), 'Canal_Final'] = 'Meta Ads'
    leads.loc[(leads['GCLID'].isnull()) & (~leads['URL'].str.contains('meta|tiktok|gads', case=False, na=False)) & (leads['SEM / SEO'] == 'SEO'), 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- CENTRO DE CONTROL ---
    with st.sidebar:
        st.header("🎮 Centro de Control")
        mes_sel = st.selectbox("📅 Mes para Fotos Fijas", ["Histórico"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True))
        sedes_sel = st.multiselect("📍 Sedes", df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Canales", df_leads['Canal_Final'].unique(), default=df_leads['Canal_Final'].unique())

    # Datos filtrados (respetando sedes y canales)
    df_base_leads = df_leads[(df_leads['Centro origen'].isin(sedes_sel)) & (df_leads['Canal_Final'].isin(canal_sel))].copy()
    
    # Datos para la "Foto Fija" (con filtro de mes)
    f_leads = df_base_leads.copy()
    f_inv = df_inv.copy()
    if mes_sel != "Histórico":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    st.title(f"🚀 Business Intelligence - Mundo Estudiante")
    
    # --- PESTAÑAS ---
    tabs = st.tabs(["🌪️ ROI Global", "🚫 No Válidos", "📉 Perdidos", "🏢 Sedes", "📞 Contacto", "🙋 Atribución", "📅 Tendencias", "📈 Evolución Mensual"])

    # 1 a 7 mantienen la lógica anterior... (se incluyen en el código completo abajo)
    with tabs[0]:
        st.header("ROI y Embudo")
        ing_t, inv_t = f_leads['Valor total'].sum(), f_inv['INVERSIÓN TOTAL'].sum()
        l_cap = len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos", f"{ing_t:,.0f}€")
        c2.metric("Inversión", f"{inv_t:,.0f}€")
        c3.metric("ROAS", f"{(ing_t/inv_t if inv_t>0 else 0):.2f}x")
        c4.metric("CAC", f"{(inv_t/l_cap if l_cap>0 else 0):.2f}€")
        st.plotly_chart(go.Figure(go.Funnel(y=["Leads", "Pruebas", "Ventas"], x=[len(f_leads), len(f_leads[f_leads['Vino a prueba'] == 'Si']), l_cap])), use_container_width=True)

    with tabs[1]:
        df_nv = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO']
        st.plotly_chart(px.pie(df_nv, names='Canal_Final', title="Inválidos por Canal"), use_container_width=True)
        st.plotly_chart(px.bar(df_nv['Centro origen'].value_counts().reset_index(), x='count', y='Centro origen', orientation='h', text_auto=True, title="Inválidos por Sede"), use_container_width=True)

    with tabs[2]:
        df_per = f_leads[f_leads['Situacion actual'] == 'CLIENTE PERDIDO']
        st.error(f"Fuga Total: {df_per['Valor total'].sum():,.0f}€")
        st.plotly_chart(px.bar(df_per['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h', text_auto=True), use_container_width=True)

    with tabs[3]:
        sede_stats = f_leads.groupby('Centro origen').agg({'Identificador':'count', 'Valor total':'sum', 'Situacion actual': lambda x: (x=='CLIENTE CAPTADO').sum()}).reset_index()
        sede_stats.columns = ['Sede', 'Leads', 'Ventas', 'Captados']
        st.plotly_chart(px.bar(sede_stats.sort_values('Ventas', ascending=False), x='Sede', y='Ventas', text_auto='.3s', color='Ventas', title="Ingresos por Sede"), use_container_width=True)
        sede_stats['%_Conv'] = (sede_stats['Captados']/sede_stats['Leads']*100).round(1)
        st.plotly_chart(px.bar(sede_stats.sort_values('%_Conv', ascending=False), x='Sede', y='%_Conv', text_auto='.1f', title="Eficiencia de Cierre (%)"), use_container_width=True)

    with tabs[4]:
        st.plotly_chart(px.bar(f_leads['Forma contacto'].value_counts().reset_index(), x='Forma contacto', y='count', text_auto=True, title="Volumen de Contacto"), use_container_width=True)
        st.plotly_chart(px.bar(f_leads.groupby('Forma contacto')['Valor total'].sum().reset_index(), x='Forma contacto', y='Valor total', text_auto='.3s', title="Ingresos por Canal de Contacto"), use_container_width=True)

    with tabs[5]:
        st.plotly_chart(px.pie(f_leads, names='Como conoce', title="Atribución"), use_container_width=True)

    with tabs[6]:
        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        st.plotly_chart(px.bar(f_leads['DIA_SEMANA'].value_counts().reindex(dias_orden).reset_index(), x='DIA_SEMANA', y='count', text_auto=True, title="Leads por Día"), use_container_width=True)

    # --- PESTAÑA 8: EVOLUCIÓN MENSUAL (HACIA ABAJO) ---
    with tabs[7]:
        st.header("📈 Evolución de Métricas Clave")
        st.info("Nota: Estos gráficos muestran la tendencia histórica completa para las Sedes y Canales seleccionados.")

        # Agregación mensual de leads
        mes_leads = df_base_leads.groupby('MES_AÑO').agg({
            'Identificador': 'count',
            'Situacion actual': lambda x: (x == 'CLIENTE CAPTADO').sum(),
            'Valor total': 'sum'
        }).reset_index().sort_values('MES_AÑO')
        
        # Agregación mensual de inversión
        mes_inv = df_inv.groupby('MES_AÑO')['INVERSIÓN TOTAL'].sum().reset_index()
        
        # Combinar datos
        evol_df = pd.merge(mes_leads, mes_inv, on='MES_AÑO', how='left').fillna(0)
        evol_df.columns = ['Mes', 'Leads', 'Clientes', 'Ingresos', 'Inversion']
        
        # Cálculos de ratios
        evol_df['ROAS'] = (evol_df['Ingresos'] / evol_df['Inversion']).replace([float('inf'), -float('inf')], 0).fillna(0)
        evol_df['CAC'] = (evol_df['Inversion'] / evol_df['Clientes']).replace([float('inf'), -float('inf')], 0).fillna(0)
        evol_df['Tasa_Conv'] = (evol_df['Clientes'] / evol_df['Leads'] * 100).fillna(0)

        # 1. Leads por Mes
        st.plotly_chart(px.bar(evol_df, x='Mes', y='Leads', text_auto=True, title="Volumen de Leads por Mes", color_discrete_sequence=['#636EFA']), use_container_width=True)
        
        # 2. Clientes por Mes
        st.plotly_chart(px.bar(evol_df, x='Mes', y='Clientes', text_auto=True, title="Captación de Clientes por Mes", color_discrete_sequence=['#00CC96']), use_container_width=True)
        
        # 3. Coste (Inversión) por Mes
        st.plotly_chart(px.bar(evol_df, x='Mes', y='Inversion', text_auto='.3s', title="Inversión en Publicidad por Mes (€)", color_discrete_sequence=['#EF553B']), use_container_width=True)
        
        # 4. ROAS por Mes
        fig_roas = px.line(evol_df, x='Mes', y='ROAS', markers=True, title="Evolución del ROAS (Retorno Inversión)")
        fig_roas.update_traces(line_color='gold', line_width=4)
        st.plotly_chart(fig_roas, use_container_width=True)
        
        # 5. CAC por Mes
        fig_cac = px.line(evol_df, x='Mes', y='CAC', markers=True, title="Evolución del CAC (Coste Adquisición Cliente)")
        fig_cac.update_traces(line_color='orchid', line_width=4)
        st.plotly_chart(fig_cac, use_container_width=True)
        
        # 6. Tasa de Conversión por Mes
        fig_tc = px.line(evol_df, x='Mes', y='Tasa_Conv', markers=True, title="Tasa de Conversión (%)")
        fig_tc.update_traces(line_color='cyan', line_width=4)
        st.plotly_chart(fig_tc, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
