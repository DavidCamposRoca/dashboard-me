import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="BI Mundo Estudiante - Pro", layout="wide")

FILE = "Datos_Estaticos_ME_V1__Canvas.xlsx"

@st.cache_data
def load_data():
    # Intento de lectura (Excel o CSV según lo que haya en el repo)
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

    # LÓGICA DE CANALES MEJORADA
    leads['Canal_Final'] = 'Otros / Orgánico'
    leads.loc[(leads['GCLID'].notnull()) | (leads['SEM / SEO'].str.contains('SEM', na=False)), 'Canal_Final'] = 'Google Ads'
    leads.loc[(leads['URL'].str.contains('meta|facebook|instagram', case=False, na=False)) | (leads['Telekos'].str.contains('facebook', case=False, na=False)), 'Canal_Final'] = 'Meta Ads'
    leads.loc[(leads['GCLID'].isnull()) & (~leads['URL'].str.contains('meta|tiktok|gads', case=False, na=False)) & (leads['SEM / SEO'] == 'SEO'), 'Canal_Final'] = 'SEO'
    
    return leads, inv

try:
    df_leads, df_inv = load_data()

    # --- SIDEBAR: CENTRO DE CONTROL ---
    with st.sidebar:
        st.title("🕹️ Intelligence Control")
        mes_sel = st.selectbox("📅 Seleccionar Periodo", ["Histórico Completo"] + sorted(df_leads['MES_AÑO'].unique(), reverse=True))
        sedes_sel = st.multiselect("📍 Filtrar por Sedes", df_leads['Centro origen'].unique(), default=df_leads['Centro origen'].unique())
        canal_sel = st.multiselect("📣 Filtrar por Canales", df_leads['Canal_Final'].unique(), default=df_leads['Canal_Final'].unique())

    # --- FILTRADO ---
    f_leads = df_leads[(df_leads['Centro origen'].isin(sedes_sel)) & (df_leads['Canal_Final'].isin(canal_sel))]
    f_inv = df_inv
    if mes_sel != "Histórico Completo":
        f_leads = f_leads[f_leads['MES_AÑO'] == mes_sel]
        f_inv = df_inv[df_inv['MES_AÑO'] == mes_sel]

    st.title(f"📈 Análisis de Negocio: {mes_sel}")

    # --- PESTAÑAS ---
    t1, t2, t3, t4, t5, t6 = st.tabs([
        "🌪️ ROI y Funnel", "🚫 Calidad (Inválidos)", "📉 Ventas Perdidas", "🏢 Sedes Pro", "📞 Canales Contacto", "🙋 Atribución"
    ])

    # PESTAÑA 1: ROI Y FUNNEL
    with t1:
        st.subheader("Rendimiento Económico y Conversión")
        l_tot = len(f_leads)
        l_pru = len(f_leads[f_leads['Vino a prueba'] == 'Si'])
        l_cap = len(f_leads[f_leads['Situacion actual'] == 'CLIENTE CAPTADO'])
        inversion = f_inv['INVERSIÓN TOTAL'].sum()
        ingresos = f_leads['Valor total'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos Totales", f"{ingresos:,.0f}€")
        c2.metric("Inversión Total", f"{inversion:,.0f}€")
        c3.metric("ROAS (Retorno)", f"{(ingresos/inversion if inversion>0 else 0):.2f}x")
        c4.metric("CAC (Coste Adquisición)", f"{(inversion/l_cap if l_cap>0 else 0):.2f}€")

        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            fig_fun = go.Figure(go.Funnel(
                y=["Leads Entrantes", "Fueron a Prueba", "Clientes Finales"],
                x=[l_tot, l_pru, l_cap],
                textinfo="value+percent initial"))
            st.plotly_chart(fig_fun, use_container_width=True)
        with col_f2:
            st.write("**Eficiencia de Prueba:**")
            ef_prueba = (l_cap / l_pru * 100) if l_pru > 0 else 0
            st.info(f"El {ef_prueba:.1f}% de los alumnos que prueban clase, se acaban matriculando.")
            st.write("**Ticket Medio:**")
            t_medio = (ingresos / l_cap) if l_cap > 0 else 0
            st.success(f"{t_medio:.2f}€ por cliente")

    # PESTAÑA 2: NO VÁLIDOS
    with t2:
        st.subheader("Análisis de Leads de Baja Calidad")
        df_nv = f_leads[f_leads['Situacion actual'] == 'LEAD NO VALIDO']
        perc_nv = (len(df_nv)/len(f_leads)*100) if len(f_leads)>0 else 0
        st.warning(f"Atención: El {perc_nv:.1f}% de tus leads actuales son 'No Válidos'.")
        
        ca1, ca2 = st.columns(2)
        with ca1:
            fig_nv1 = px.bar(df_nv.groupby('Canal_Final').size().reset_index(), x='Canal_Final', y=0, title="Inválidos por Canal (¿Quién trae basura?)", labels={0:'Cant'})
            st.plotly_chart(fig_nv1, use_container_width=True)
        with ca2:
            fig_nv2 = px.pie(df_nv, names='Forma contacto', title="Inválidos por Forma de Contacto")
            st.plotly_chart(fig_nv2, use_container_width=True)

    # PESTAÑA 3: PERDIDOS (COSTE DE OPORTUNIDAD)
    with t3:
        st.subheader("Fuga de Ingresos")
        df_per = f_leads[f_leads['Situacion actual'] == 'CLIENTE PERDIDO']
        v_perdido = df_per['Valor total'].sum() # O podrías usar ticket medio
        st.error(f"Coste de Oportunidad (Ventas no cerradas): {v_perdido:,.0f}€")
        
        cp1, cp2 = st.columns(2)
        with cp1:
            fig_per1 = px.bar(df_per['Causa perdido'].value_counts().head(10).reset_index(), x='count', y='Causa perdido', orientation='h', title="¿Por qué perdemos clientes?")
            st.plotly_chart(fig_per1, use_container_width=True)
        with cp2:
            fig_per2 = px.box(df_per, x='Canal_Final', y='Total contactos', title="Nº de Contactos antes de perder el lead")
            st.plotly_chart(fig_per2, use_container_width=True)

    # PESTAÑA 4: SEDES PRO
    with t4:
        st.subheader("Ranking de Rendimiento por Sede")
        sede_stats = f_leads.groupby('Centro origen').agg({
            'Identificador': 'count',
            'Valor total': 'sum'
        }).reset_index()
        sede_stats['Venta Media'] = sede_stats['Valor total'] / sede_stats['Identificador']
        
        st.dataframe(sede_stats.sort_values('Valor total', ascending=False), use_container_width=True)
        st.plotly_chart(px.scatter(sede_stats, x='Identificador', y='Valor total', size='Venta Media', text='Centro origen', title="Volumen vs Rentabilidad por Sede"), use_container_width=True)

    # PESTAÑA 5: CONTACTO
    with t5:
        st.subheader("Análisis de Canales de Entrada")
        fig_cont = px.sunburst(f_leads, path=['Forma contacto', 'Situacion actual'], values='Valor total', title="Efectividad de Forma de Contacto vs Ventas")
        st.plotly_chart(fig_cont, use_container_width=True)

    # PESTAÑA 6: ATRIBUCIÓN
    with t6:
        st.subheader("Atribución de Marketing")
        col_at1, col_at2 = st.columns(2)
        with col_at1:
            st.write("**¿Cómo nos conocen realmente?**")
            st.plotly_chart(px.pie(f_leads, names='Como conoce', hole=0.3))
        with col_at2:
            st.write("**Top URLs de Origen (Valor generado)**")
            url_val = f_leads.groupby('URL')['Valor total'].sum().sort_values(ascending=False).head(10).reset_index()
            st.dataframe(url_val)

except Exception as e:
    st.error(f"Error en la carga de datos: {e}")
