import streamlit as st
import requests
from PIL import Image
import pandas as pd
from langchain.chat_models import ChatOpenAI
#from study_agents_rag import StudyOrchestrator
import study_agents_rag
from dotenv import load_dotenv
import os
from utils.funciones_streamlit import *


# Configuración de la página
st.set_page_config(page_title="Chat Interactivo", page_icon=":books:", layout="wide")


st.markdown("""
<style>
/* Fondo en degradado */
.stApp {
    background: linear-gradient(135deg,#b9252f, #be1e28, #960a16, #40060c);
    color: white;
    font-family: 'Arial', sans-serif;
}
            
/* Selectbox del menú en sidebar */
[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div[class*="selectbox"] {
    background-color: white !important;
    color: black !important;
}
            
/* Cabecera en negro y blanco */
.header {
    background-color: black;
    padding: 15px;
    color: white;
    text-align: center;
    font-size: 32px; /* Tamaño aumentado */
    font-weight: bold;
    font-family: 'Arial', sans-serif;
    border-radius: 10px;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5); /* Sombra de texto */
}

.subheader {
    background-color: white;
    padding: 10px;
    text-align: center;
    font-size: 24px; /* Tamaño aumentado */
    font-weight: bold;
    color: black;
    font-family: 'Arial', sans-serif;
    border-radius: 10px;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3); /* Sombra más suave */
}
            
/* Sidebar en negro */
.css-1d391kg, .css-1lcbmhc, .css-1d391kg e1fqkh3o4 {
    background-color: black !important;
    color: white !important;
}

/* Botones y formularios */
.stTextInput, .stTextArea, .stSelectbox, .stButton {
    font-family: 'Arial', sans-serif;
    color: black !important;
    background-color: white !important;
    border-radius: 10px;
    padding: 10px;
    border: none;
    box-shadow: 2px 2px 5px black;
}

.stButton>button {
    background-color: #da2f3a!important;
    color: white !important;
    font-weight: bold;
    border-radius: 10px;
}

/* Alertas y subencabezados */
.stSuccess {
    color: black !important;
}

.stSubheader {
    color: white !important;
}

.stAlert-success {
    color: black !important;
}

/* Botón de Cerrar Sesión */
.css-1d391kg button {
    position: absolute;
    top: 20px;
    left: 20px;
    background-color: #da2f3a;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    padding: 10px;
}
/* Color del texto de placeholder en negro */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
.stSelectbox div[data-baseweb="select"] input::placeholder {
    color: black !important;
    opacity: 1 !important;
}

/* Para navegadores específicos */
.stTextInput input:-ms-input-placeholder,
.stTextArea textarea:-ms-input-placeholder {
    color: black !important;
}

.stTextInput input::-ms-input-placeholder,
.stTextArea textarea::-ms-input-placeholder {
    color: black !important;
}
/* Sidebar - Fondo negro y texto blanco (override modo oscuro) */
[data-testid="stSidebar"] {
    background-color: black !important;
    color: white !important;
}

/* Mensajes del chat - texto en negro */
[data-testid="stChatMessageContent"] p,
[data-testid="stMarkdownContainer"] p,
.stMarkdown p {
    color: black !important;
}

/* Input del chat (cuadro de texto) */
[data-testid="stChatInput"] textarea {
    color: black !important;
    background-color: white !important;
}

/* Placeholder del input del chat */
[data-testid="stChatInput"] textarea::placeholder {
    color: black !important;
    opacity: 1 !important;
}
            /* Botones de descarga en el sidebar */
[data-testid="stSidebar"] .stDownloadButton > button {
    background-color: rgba(255, 255, 255, 0.5) !important;  /* Blanco con 30% de opacidad */
    color: white !important;
    border: 2px solid white !important;
    backdrop-filter: blur(5px);  /* Efecto de vidrio */
    transition: all 0.3s ease;
}

/* Efecto hover */
[data-testid="stSidebar"] .stDownloadButton > button:hover {
    background-color: rgba(255, 255, 255, 0.5) !important;
    transform: scale(1.05);
}

/* Efecto al hacer click */
[data-testid="stSidebar"] .stDownloadButton > button:active {
    background-color: rgba(255, 255, 255, 0.7) !important;
}

/* Texto del botón */
[data-testid="stSidebar"] .stDownloadButton > button span {
    color: white !important;
    font-weight: bold;
}

</style>

""", unsafe_allow_html=True)

load_dotenv()
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY"),
index_name_pinecone_ds=os.getenv("index_name_pinecone_ds"),
index_name_pinecone_fs=os.getenv("index_name_pinecone_fs"),
index_name_pinecone_pdf=os.getenv("index_name_pinecone_pdf"),
MISTRAL_API_KEY=os.getenv("MISTRAL_API_KEY"),
OpenAI_API_KEY=os.getenv("OpenAI_API_KEY")

# Estilos personalizados
#load_css("utils/style.css")

# Mostrar el logo
logo_image = Image.open("src/img/thebridg.jpg")

# Contenedor principal
title_container = st.container()
with title_container:
    st.markdown('<div class="header" style="color: white !important; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);">BIBAI</div>', 
    unsafe_allow_html=True)
    st.markdown('<div class="subheader">Plataforma de aprendizaje The Bridge</div>', unsafe_allow_html=True)
# Sidebar para el menu de la app

with st.sidebar:
    st.image(logo_image, use_container_width=True)
    st.markdown("### Menú")
    menu_option = st.selectbox("Selecciona una opción", ["Inicio", "Perfil"],key="main_menu",
                             on_change=lambda: st.session_state.pop("current_page", None))

    # Botón de "Cerrar sesión" en la esquina superior izquierda
    if st.button("Cerrar sesión"):
        # Limpiar el estado de la sesión
        st.session_state.clear()
        st.rerun()  # Reiniciar la aplicación
        

# Interfaz de chat
st.header("Chat con el TA")
# Iniciar sesión y mostrar perfil


# Paso 1: Login del alumno
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    email = st.text_input("Introduce tu email para iniciar sesión:")
    if email:
        login_data = login(email)
        if login_data:
            st.session_state["id_sesion"] = login_data["id_sesion"]
            st.session_state["email"] = email
            st.session_state["alumno"] = login_data["alumno"]
            st.session_state.authenticated = True
            st.success(f"¡Bienvenido, {login_data['alumno']['nombre']}!")
            st.rerun()
# Si está autenticado, mostrar la página correspondiente

if menu_option == "Perfil":
    mostrar_perfil()
# Paso 2: Selección de vertical o career
if st.session_state.authenticated and "alumno" in st.session_state:
    opciones = obtener_opciones(st.session_state["email"])
    if opciones:
        seleccion = st.selectbox("Elige tu vertical o career:", [""] + opciones)
        if seleccion:
            st.session_state["seleccion"] = seleccion
            st.success(f"Has seleccionado: {seleccion}")

# Paso 3: Selección de módulo
if "seleccion" in st.session_state and st.session_state["seleccion"]:
    modulos, modulos_ids = obtener_modulos(st.session_state["seleccion"], st.session_state["email"])
    if modulos:
        modulo_seleccionado = st.selectbox("Elige un módulo:", [""] + modulos)
        if modulo_seleccionado:
            st.session_state["modulo_seleccionado"] = modulo_seleccionado
            st.session_state["modulo_id"] = modulos_ids[modulos.index(modulo_seleccionado)]
            st.success(f"Has seleccionado el módulo: {modulo_seleccionado}")

# Paso 4: Selección de tema (unidad)
if "modulo_seleccionado" in st.session_state and st.session_state["modulo_seleccionado"]:
    unidades, unidades_ids = obtener_unidades(st.session_state["modulo_seleccionado"])
    if unidades:
        unidad_seleccionada = st.selectbox("Elige un tema:", [""] + unidades)
        if unidad_seleccionada:
            st.session_state["unidad_seleccionada"] = unidad_seleccionada
            st.session_state["unidad_id"] = unidades_ids[unidades.index(unidad_seleccionada)]
            st.success(f"Has seleccionado el tema: {unidad_seleccionada}")

# Paso 5: Generar resumen del tema seleccionado para descargar
if "unidad_seleccionada" in st.session_state and st.session_state["unidad_seleccionada"]:
    if st.button("Generar resumen del tema"):
        resumen = generar_resumen(
            st.session_state["seleccion"],
            st.session_state["modulo_id"],
            st.session_state["unidad_id"]
        )
        st.session_state["resumen"] = resumen
        if resumen:
            # Se genera el PDF sin mostrar el resumen en pantalla
            pdf_bytes = generar_pdf(resumen)
            st.session_state.update({
                "resumen_pdf": pdf_bytes,
                "resumen_count": st.session_state.get("resumen_count", 0) + 1
            })
            st.rerun()
    sidebar_dynamic()
            
            
    
#----------------------------------------------------------------------
#----------------------------------------------------------------------

#Paso 6: Llama a generar tipo de ayuda para seleccionar
if st.session_state.get("resumen_pdf"):
    vertical = "Career Readiness" if st.session_state["seleccion"] == "Career Readiness" else st.session_state["seleccion"]
    
    
    opciones_ayuda_raw = obtener_ayudas(vertical)  # Lista de diccionarios
    opciones_ayuda = [opcion["tipo_ayuda"] for opcion in opciones_ayuda_raw] 

    if opciones_ayuda_raw:
        # Extraer solo los valores de "tipo_ayuda"
        opciones_ayuda = [opcion["tipo_ayuda"] for opcion in opciones_ayuda_raw]
        
        ayuda_seleccionada = st.selectbox("Elige una ayuda:", [""] + opciones_ayuda)
        
        if ayuda_seleccionada:
            st.session_state["ayuda_seleccionada"] = {"tipo_ayuda": ayuda_seleccionada}
            st.success(f"Has seleccionado la ayuda: {ayuda_seleccionada}")
            st.session_state.ayuda_seleccionada = ayuda_seleccionada
            help_type = ayuda_seleccionada
            
            if help_type == "Análisis de CV":
                    uploaded_file = st.file_uploader("Sube tu CV", type="pdf")
                    
                    if uploaded_file and st.button("Analizar CV"):
                        with st.spinner("Analizando..."):
                            try:
                                st.session_state.analysis = analyze_cv(uploaded_file)
                                st.session_state["analysis_count"] = st.session_state.get("analysis_count", 0) + 1  # Incremento seguro
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error en el análisis: {str(e)}")
                                st.session_state.analysis = None
                    
                    if st.session_state.get("cv_analysis"):
                        st.subheader("🔍 Resultado del Análisis")
                        st.write(st.session_state.cv_analysis)
                        st.markdown(f"```text\n{st.session_state.analysis}\n```")
                        
                        # Finalizar ejecución aquí
                        st.markdown("---")
                        st.markdown("© 2025 The Bridge. Confía en el proceso ❤️.") 
                        st.stop()   
    # Llamar a sidebar_dynamic FUERA del bloque condicional
            sidebar_dynamic_cv()
#----------------------------------------------------------------------
#inicializaciones necesarias para el funcionamiento de los agentes

llm = ChatOpenAI(
    model_name="gpt-4-turbo-preview",
    temperature=0.7,
    api_key=os.getenv("OpenAI_API_KEY")
)

# Inicializar el orquestador
st.session_state.orchestrator = study_agents_rag.StudyOrchestrator(llm)

# Inicializar otras variables de sesión
if 'current_response' not in st.session_state:
    st.session_state.current_response = None
if 'rag_results' not in st.session_state:
    st.session_state.rag_results = None
if 'last_help_type' not in st.session_state:
    st.session_state.last_help_type = None
if 'last_query' not in st.session_state:
    st.session_state.last_query = None
if 'show_solution' not in st.session_state:
    st.session_state.show_solution = False
if 'cv_analysis' not in st.session_state:
    st.session_state.cv_analysis = None
if 'progress_text' not in st.session_state:
    st.session_state.progress_text = ""
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
#----------------------------------------------------------------------
module_map = {
    "Data Science": "ds",
    "Full Stack": "fs",
    "Career Readiness": "both"
}

# Paso 7: El alumno introduce su duda en un cuadro de texto
#----------------------------------------------------------------------
if st.session_state.get("resumen_pdf") and st.session_state.get("ayuda_seleccionada") != "Análisis de CV":
    query = st.text_input("Introduce tu duda:")
    
    if query:  # Solo procesar si hay una duda escrita
        # Obtener el tipo de ayuda con valor por defecto si no existe
        ayuda_seleccionada = st.session_state.get(
            "ayuda_seleccionada", 
            "Ayuda general"  # Valor por defecto
        )
        
        # Llamar a la función de procesamiento
        response = process_query(query,st.session_state["seleccion"],module_map,ayuda_seleccionada)
        # Actualizar el estado de la sesión
        st.session_state.current_response = response
        st.session_state.last_help_type = ayuda_seleccionada
        st.session_state.last_query = query

# Mostrar la respuesta si existe
if st.session_state.current_response:
    if st.session_state.last_help_type == "Ejercicios prácticos":
        st.markdown("### 📝 Contenido del Ejercicio")
        display_practice_content(st.session_state.current_response)
    else:
        st.markdown("### 📝 Respuesta:")
        st.markdown(st.session_state.current_response)

#----------------------------------------------------------------------
#----------------------------------------------------------------------

# Pie de página
st.markdown("---")
st.markdown("© 2025 The Bridge. Confía en el proceso ❤️.")