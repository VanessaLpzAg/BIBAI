import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from utils.funciones_streamlit import load_custom_css, display_header, generate_graphs, get_session_data, authenticate_teacher

# Configuración de la página
def main_dashboard():
    st.set_page_config(page_title="📊 Teacher Dashboard", layout="wide")
    
    # Cargar CSS personalizado
    load_custom_css()

    # Mostrar logo en la barra lateral
    with st.sidebar:
        logo = Image.open("src/img/logo_blanco.png")
        st.image(logo, width=150, output_format="PNG")

    # Inicializar sesión
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None

    # Login
    if not st.session_state.authenticated:
        login_page()
    else:
        # Mostrar la cabecera con borde blanco
        display_header()

        # Obtener datos del usuario
        df = get_session_data(st.session_state.user['id'])

        if df.empty:
            st.warning("No data available for your bootcamps.")
        else:
            # Filtros
            st.sidebar.header("Filtros")
            bootcamp_options = df['bootcamp'].unique()
            month_options = df['mes'].unique()

            selected_bootcamp = st.sidebar.multiselect("Elige Bootcamp", options=bootcamp_options, default=bootcamp_options)
            selected_month = st.sidebar.multiselect("Elige Mes/Año", options=month_options, default=month_options)

            # Aplicar filtros
            if selected_bootcamp or selected_month:
                mask = pd.Series(True, index=df.index)
                if selected_bootcamp:
                    mask &= df['bootcamp'].isin(selected_bootcamp)
                if selected_month:
                    mask &= df['mes'].isin(selected_month)
                df = df[mask]

            if df.empty:
                st.warning("No hay datos para los filtros seleccionados.")
            else:
                # Generar gráficos
                generate_graphs(df)

                # Mostrar los detalles de la tabla
                st.header("Detalle")
                st.dataframe(df)


# Página de login
def login_page():
    st.image("src/img/BIBAI.png", width=200, output_format="PNG", use_container_width=False)
    st.title("Teacher Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            user = authenticate_teacher(email)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.success(f"Welcome, {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid email")


if __name__ == "__main__":
    main_dashboard()
