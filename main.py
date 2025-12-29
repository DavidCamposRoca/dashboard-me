import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Mundo Estudiante - Business Intelligence", layout="wide")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
    inv = pd.read_excel(FILE, sheet_name='Inversion')
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- SELECTORES LATERALES ---
    with st.sidebar:
        st.title("Configuración")
        mes_sel = st.selectbox("Mes", ["Todos"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True))
        centros = st.multiselect("Centros", df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())

    # Filtrado base
    df_f_leads = df_leads[df_leads['Centro origen'].isin(centros)]
    df_f_inv = df_inv
    if mes_sel != "Todos":
        df_f_leads = df_f_leads[df_f_leads['MES_AÑO'] == mes_sel]
        df_f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    # --- CREACIÓN DE PESTAÑAS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 General", "🔍 Google Ads", "📱 Meta (FB/IG)", "📈 SEO / Orgánico"])

    # --- TABS 1: GENERAL ---
    with tab1:
        st.header("Visión Global del Negocio")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Leads", len(df_f_leads))
        c2.metric("Inversión Total", f"{df_f_inv['INVERSIÓN TOTAL'].sum():,.2f} €")
        c3.metric("Ingresos Totales", f"{df_f_leads['Valor total'].sum():,.2f} €")
        
        st.plotly_chart(px.line(df_f_leads.groupby('MES_AÑO').size().reset_index(), x='MES_AÑO', y=0, title="Tendencia de Captación"), use_container_width=True)

    # --- TABS 2: GOOGLE ADS ---
    with tab2:
        st.header("Rendimiento Google Ads")
        # Lógica: GCLID existe o marca SEM
        gads = df_f_leads[(df_f_leads['GCLID'].notnull()) | (df_f_leads['SEM / SEO'] == 'SEM')]
        inversion_gads = df_f_inv['INVERSIÓN EN G ADS'].sum()
        
        c1, c2, c4 = st.columns(3)
        c1.metric("Leads GAds", len(gads))
        c2.metric("Inversión", f"{inversion_gads:,.2f} €")
        c4.metric("CPL", f"{(inversion_gads/len(gads)) if len(gads)>0 else 0:.2f} €")
        
        st.plotly_chart(px.bar(gads['Centro origen'].value_counts().reset_index(), x='Centro origen', y='count', title="Leads GAds por Centro"), use_container_width=True)

    # --- TABS 3: META ---
    with tab3:
        st.header("Rendimiento Meta (Facebook/Instagram)")
        # Lógica: Basado en inversión de Meta y origen conocido
        inversion_meta = df_f_inv['INVERSIÓN EN META'].sum()
        st.metric("Inversión en Meta", f"{inversion_meta:,.2f} €")
        st.info("Aquí puedes filtrar por 'Como conoce' == 'Facebook' o 'Instagram'")

    # --- TABS 4: SEO ---
    with tab4:
        st.header("Rendimiento SEO (Tráfico Gratis)")
        # Lógica: El campo SEM / SEO dice SEO
        seo_leads = df_f_leads[df_f_leads['SEM / SEO'] == 'SEO']
        
        c1, c2 = st.columns(2)
        c1.metric("Leads SEO", len(seo_leads))
        c2.metric("Coste SEO", "0.00 €", help="El SEO es captación orgánica sin pago directo por lead")
        
        st.write("### Top Páginas de Entrada SEO")
        st.dataframe(seo_leads['URL'].value_counts().head(10))

except Exception as e:
    st.error(f"Error: {e}")
