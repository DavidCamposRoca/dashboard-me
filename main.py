import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Mundo Estudiante - Intelligence Hub", layout="wide")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
    inv = pd.read_excel(FILE, sheet_name='Inversion')
    
    # Limpieza y Formato
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')
    
    # --- LÓGICA DE CANALES ---
    # 1. Google Ads: GCLID existe o SEM en la columna
    leads['is_gads'] = (leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False))
    
    # 2. Meta: META en URL o facebook en Telekos
    leads['is_meta'] = (leads['URL'].str.contains('meta|facebook', case=False, na=False)) | \
                       (leads['Telekos'].str.contains('facebook', case=False, na=False))
    
    # 3. SEO: Sin GCLID, sin marcas de ads en URL y marcado como SEO
    leads['is_seo'] = (leads['GCLID'].isnull()) & \
                      (~leads['URL'].str.contains('meta|tiktok|gads|gad_|gbraid|wbraid', case=False, na=False)) & \
                      (leads['SEM / SEO'] == 'SEO')
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    st.title("🚀 Business Intelligence - Mundo Estudiante")
    
    # --- FILTROS LATERALES ---
    with st.sidebar:
        st.header("Segmentación")
        meses = ["Todos"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True)
        mes_sel = st.selectbox("Selecciona Mes", meses)
        centros = st.multiselect("Centros", df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())

    # Filtrado Dinámico
    f_leads = df_leads[df_leads['Centro origen'].isin(centros)]
    f_inv = df_inv
    if mes_sel != "Todos":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    # --- PESTAÑAS ---
    tab_gen, tab_gads, tab_meta, tab_seo = st.tabs(["📊 Global", "🔍 Google Ads", "📱 Meta Ads", "📈 SEO"])

    def mostrar_metricas(df, inversion, titulo):
        leads_n = len(df)
        clientes = len(df[df['Situacion actual'] == 'CLIENTE CAPTADO'])
        ingresos = df['Valor total'].sum()
        
        cr = (clientes / leads_n * 100) if leads_n > 0 else 0
        cpl = (inversion / leads_n) if leads_n > 0 else 0
        roas = (ingresos / inversion) if inversion > 0 else 0
        
        st.subheader(f"Métricas {titulo}")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Leads", f"{leads_n:,}")
        c2.metric("Clientes", f"{clientes}")
        c3.metric("CR (Conv.)", f"{cr:.1f}%")
        c4.metric("CPL", f"{cpl:.2f} €")
        c5.metric("ROAS", f"{roas:.2f}x")
        
        # Gráficos de apoyo
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(df, names='Situacion actual', title="Embudo de Estados", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            fig_bar = px.bar(df['Centro origen'].value_counts().reset_index(), x='Centro origen', y='count', title="Leads por Centro")
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- CONTENIDO DE PESTAÑAS ---
    with tab_gen:
        st.header("Resumen Multicanal")
        total_inv = f_inv['INVERSIÓN TOTAL'].sum()
        mostrar_metricas(f_leads, total_inv, "Totales")

    with tab_gads:
        df_g = f_leads[f_leads['is_gads']]
        inv_g = f_inv['INVERSIÓN EN G ADS'].sum()
        mostrar_metricas(df_g, inv_g, "Google Ads")

    with tab_meta:
        df_m = f_leads[f_leads['is_meta']]
        inv_m = f_inv['INVERSIÓN EN META'].sum()
        mostrar_metricas(df_m, inv_m, "Meta Ads")

    with tab_seo:
        df_s = f_leads[f_leads['is_seo']]
        # El SEO no tiene inversión directa en este modelo
        st.header("Métricas SEO (Orgánico)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Leads Orgánicos", f"{len(df_s):,}")
        c2.metric("Clientes SEO", f"{len(df_s[df_s['Situacion actual'] == 'CLIENTE CAPTADO'])}")
        c3.metric("Valor Generado", f"{df_s['Valor total'].sum():,.2f} €")
        
        st.write("### Top URLs que generan Leads SEO")
        st.dataframe(df_s['URL'].value_counts().head(10))

except Exception as e:
    st.error(f"Error en los datos: {e}")
