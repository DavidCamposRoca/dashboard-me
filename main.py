import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Mundo Estudiante - Master BI", layout="wide", initial_sidebar_state="expanded")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    # Intentar cargar Excel
    try:
        leads = pd.read_excel(FILE, sheet_name='Total_Datos_ME')
        inv = pd.read_excel(FILE, sheet_name='Inversion')
    except:
        # Si falla el Excel, intentamos con CSV por si acaso
        leads = pd.read_csv('Datos_Estaticos_ME_V1__Canvas.xlsx - Total_Datos_ME.csv')
        inv = pd.read_csv('Datos_Estaticos_ME_V1__Canvas.xlsx - Inversion.csv')
    
    leads['PERIODO'] = pd.to_datetime(leads['PERIODO'])
    inv['PERIODO'] = pd.to_datetime(inv['PERIODO'])
    leads['MES_AÑO'] = leads['PERIODO'].dt.strftime('%Y-%m')
    inv['MES_AÑO'] = inv['PERIODO'].dt.strftime('%Y-%m')

    # LÓGICA DE CANALES
    leads['Canal_Final'] = 'Otros'
    mask_gads = (leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False))
    leads.loc[mask_gads, 'Canal_Final'] = 'Google Ads'
    
    mask_meta = (leads['URL'].str.contains('meta|facebook', case=False, na=False)) | \
                (leads['Telekos'].str.contains('facebook', case=False, na=False))
    leads.loc[mask_meta, 'Canal_Final'] = 'Meta Ads'
    
    mask_seo = (leads['GCLID'].isnull()) & \
               (~leads['URL'].str.contains('meta|tiktok|gads|gad_|gbraid|wbraid', case=False, na=False)) & \
               (leads['SEM / SEO'] == 'SEO')
    leads.loc[mask_seo, 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- SELECTORES LATERALES ---
    with st.sidebar:
        st.image("https://www.mundoestudiante.com/wp-content/uploads/2020/09/logo-mundo-estudiante.png", width=200)
        st.title("Centro de Control")
        meses = ["Todo el Histórico"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True)
        mes_sel = st.selectbox("📅 Periodo Temporal", meses)
        centro_sel = st.multiselect("📍 Centros", options=df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Canal de Captación", options=['Google Ads', 'Meta Ads', 'SEO', 'Otros'], default=['Google Ads', 'Meta Ads', 'SEO', 'Otros'])

    # --- FILTRADO ---
    f_leads = df_leads[(df_leads['Centro origen'].isin(centro_sel)) & (df_leads['Canal_Final'].isin(canal_sel))]
    f_inv = df_inv
    if mes_sel != "Todo el Histórico":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    st.title(f"🚀 Business Intelligence: {mes_sel}")
    
    # --- PESTAÑAS ---
    tab_gen, tab_gads, tab_meta, tab_seo, tab_invalid = st.tabs([
        "📊 Global", "🔍 Google Ads", "📱 Meta Ads", "📈 SEO", "❌ Leads No Válidos"
    ])

    def render_metrics(df, inversion, titulo):
        l_tot = len(df)
        l_cap = len(df[df['Situacion actual'] == 'CLIENTE CAPTADO'])
        l_inv = len(df[df['Situacion actual'] == 'LEAD NO VALIDO'])
        l_pru = len(df[df['Vino a prueba'] == 'Si'])
        val = df['Valor total'].sum()
        
        # Corrección del Error de Sintaxis aquí:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Leads", f"{l_tot}")
        c2.metric("A Prueba", f"{l_pru}", f"{(l_pru/l_tot*100) if l_tot>0 else 0:.1f}%")
        c3.metric("Captados", f"{l_cap}", f"{(l_cap/l_tot*100) if l_tot>0 else 0:.1f}%")
        c4.metric("Inválidos", f"{l_inv}", f"{(l_inv/l_tot*100) if l_tot>0 else 0:.1f}%", delta_color="inverse")
        c5.metric("Valor Total", f"{val:,.0f} €")

    with tab_gen:
        render_metrics(f_leads, f_inv['INVERSIÓN TOTAL'].sum(), "Global")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(f_leads, names='Situacion actual', title="Estados de Leads", hole=0.4), use_container_width=True)
        with col2:
            st.plotly_chart(px.bar(f_leads['Como conoce'].value_counts().head(10).reset_index(), x='count', y='Como conoce', orientation='h', title="Origen Atribución"), use_container_width=True)

    with tab_gads:
        df_g = f_leads[f_leads['Canal_Final'] == 'Google Ads']
        inv_g = f_inv['INVERSIÓN EN G ADS'].sum()
        render_metrics(df_g, inv_g, "Google Ads")
        if inv_g > 0 and len(df_g) > 0:
            st.info(f"ROAS Estimado GAds: {(df_g['Valor total'].sum() / inv_g):.2f}x  |  CPL: {(inv_g / len(df_g)):.2f}€")

    with tab_meta:
        df_m = f_leads[f_leads['Canal_Final'] == 'Meta Ads']
        inv_m = f_inv['INVERSIÓN EN META'].sum()
        render_metrics(df_m, inv_m, "Meta Ads")

    with tab_seo:
        df_s = f_leads[f_leads['Canal_Final'] == 'SEO']
        st.subheader("Rendimiento Orgánico")
        render_metrics(df_s, 0, "SEO")
        st.write("### Páginas con más captación SEO")
        st.dataframe(df_s['URL'].value_counts().head(10))

    with tab_invalid:
        st.header("Análisis de Leads No Válidos")
        df_no_val = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO']
        
        if len(df_no_val) > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.pie(df_no_val, names='Canal_Final', title="Inválidos por Canal"), use_container_width=True)
            with col2:
                st.plotly_chart(px.bar(df_no_val['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h', title="Causas de Invalidez"), use_container_width=True)
        else:
            st.success("No se han detectado leads no válidos con los filtros actuales.")

except Exception as e:
    st.error(f"Error en el procesamiento: {e}")
