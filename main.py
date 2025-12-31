import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="ME - Intelligence Suite", layout="wide", initial_sidebar_state="expanded")

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

    # Lógica de Canales Robusta
    leads['Canal_Final'] = 'Otros / Orgánico'
    leads.loc[(leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False)), 'Canal_Final'] = 'Google Ads'
    leads.loc[(leads['URL'].str.contains('meta|facebook|instagram', case=False, na=False)) | (leads['Telekos'].str.contains('facebook', case=False, na=False)), 'Canal_Final'] = 'Meta Ads'
    leads.loc[(leads['GCLID'].isnull()) & (~leads['URL'].str.contains('meta|tiktok|gads', case=False, na=False)) & (leads['SEM / SEO'] == 'SEO'), 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- SIDEBAR (CENTRO DE CONTROL) ---
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

    # --- MÉTRICAS DE CABECERA ---
    l_tot, l_pru, l_cap = len(f_leads), len(f_leads[f_leads['Vino a prueba'] == 'Si']), len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
    ing_t, inv_t = f_leads['Valor total'].sum(), f_inv['INVERSIÓN TOTAL'].sum()
    
    st.title(f"📈 Análisis Estratégico: {mes_sel}")
    
    # --- PESTAÑAS ---
    t1, t2, t3, t4, t5, t6 = st.tabs(["🌪️ ROI y Funnel", "🚫 No Válidos", "📉 Perdidos", "🏢 Sedes", "📞 Contacto", "🙋 Atribución"])

    # 1. ROI Y FUNNEL (Doblamos la información)
    with t1:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Ingresos", f"{ing_t:,.0f}€")
        c2.metric("Inversión", f"{inv_t:,.0f}€")
        c3.metric("ROAS", f"{(ing_t/inv_t if inv_t>0 else 0):.2f}x")
        c4.metric("Ticket Medio", f"{(ing_t/l_cap if l_cap>0 else 0):.2f}€")
        c5.metric("CAC", f"{(inv_t/l_cap if l_cap>0 else 0):.2f}€")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("### Flujo de Conversión")
            fig_f = go.Figure(go.Funnel(y=["Leads", "Pruebas", "Ventas"], x=[l_tot, l_pru, l_cap], textinfo="value+percent initial"))
            st.plotly_chart(fig_f, use_container_width=True)
        with col2:
            st.write("### Eficiencia")
            st.write(f"**Tasa Conversión Global:** {(l_cap/l_tot*100 if l_tot>0 else 0):.1f}%")
            st.write(f"**Éxito en Pruebas:** {(l_cap/l_pru*100 if l_pru >0 else 0):.1f}%")
            st.progress(l_cap/l_pru if l_pru > 0 else 0)

    # 2. NO VÁLIDOS (Profundizamos)
    with t2:
        df_nv = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO'].copy()
        st.subheader(f"Análisis de leads descartados ({len(df_nv)} leads)")
        
        ca1, ca2, ca3 = st.columns(3)
        with ca1:
            st.plotly_chart(px.pie(df_nv, names='Canal_Final', title="Descartes por Canal", hole=0.3), use_container_width=True)
        with ca2:
            st.plotly_chart(px.bar(df_nv['Causa perdido'].value_counts().reset_index(), x='count', y='Causa perdido', orientation='h', title="Motivos Técnicos"), use_container_width=True)
        with ca3:
            st.plotly_chart(px.pie(df_nv, names='Centro origen', title="Descartes por Sede"), use_container_width=True)

    # 3. PERDIDOS (Añadimos Valor perdido)
    with t3:
        df_per = f_leads[f_leads['Situacion actual'] == 'CLIENTE PERDIDO'].copy()
        st.error(f"⚠️ Dinero que se ha escapado: {df_per['Valor total'].sum():,.0f}€")
        
        cp1, cp2 = st.columns(2)
        with cp1:
            st.write("### ¿Por qué perdemos clientes?")
            fig_p1 = px.bar(df_per['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h', color='count', color_continuous_scale='Reds')
            st.plotly_chart(fig_p1, use_container_width=True)
        with cp2:
            st.write("### ¿En qué momento se pierden?")
            fig_p2 = px.pie(df_per, names='Vino a prueba', title="¿Habían venido a prueba antes de perderlos?")
            st.plotly_chart(fig_p2, use_container_width=True)

    # 4. SEDES (Ranking completo)
    with t4:
        sede_metrics = f_leads.groupby('Centro origen').agg({'Identificador':'count', 'Valor total':'sum', 'Vino a prueba': lambda x: (x=='Si').sum()}).reset_index()
        sede_metrics.columns = ['Sede', 'Leads', 'Ingresos', 'Pruebas']
        sede_metrics['Ratio Conversión'] = (sede_metrics['Ingresos'] / sede_metrics['Leads']).round(2)
        
        st.write("### Tabla Comparativa de Rendimiento")
        st.dataframe(sede_metrics.sort_values('Ingresos', ascending=False), use_container_width=True)
        
        st.plotly_chart(px.scatter(sede_metrics, x='Leads', y='Ingresos', size='Pruebas', text='Sede', color='Ratio Conversión', title="Matriz Eficiencia Sedes"), use_container_width=True)

    # 5. CONTACTO (Limpieza de errores)
    with t5:
        st.write("### Efectividad según Canal de Comunicación")
        df_cont = f_leads.dropna(subset=['Forma contacto', 'Situacion actual'])
        fig_c1 = px.bar(df_cont, x="Forma contacto", color="Situacion actual", title="Volumen de Estados por Forma de Contacto", barmode='group')
        st.plotly_chart(fig_c1, use_container_width=True)
        
        fig_c2 = px.box(df_leads, x="Forma contacto", y="Valor total", title="Valor de los Leads según cómo contactan")
        st.plotly_chart(fig_c2, use_container_width=True)

    # 6. ATRIBUCIÓN (Detalle máximo)
    with t6:
        st.write("### Origen del Cliente")
        cat1, cat2 = st.columns(2)
        with cat1:
            st.plotly_chart(px.pie(f_leads, names='Como conoce', title="Atribución Declarada", hole=0.3), use_container_width=True)
        with cat2:
            top_urls = f_leads.groupby('URL')['Valor total'].sum().reset_index().sort_values('Valor total', ascending=False).head(10)
            st.write("### Top 10 URLs por Facturación")
            st.table(top_urls)

except Exception as e:
    st.error(f"Error técnico detectado: {e}")
