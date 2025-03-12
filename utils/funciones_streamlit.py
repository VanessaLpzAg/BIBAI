#IMPORTACIONES endpoints
import streamlit as st
import requests
#IMPORTACIONES dashboard
import os
import pandas as pd
import plotly.express as px
import pymysql
from datetime import datetime
from study_agents_rag_v3 import StudyOrchestrator
#IMPORTACIONES CV
from pinecone import Pinecone,ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_mistralai import MistralAIEmbeddings, ChatMistralAI
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain.prompts import ChatPromptTemplate
import tempfile
#IMPORTACIONES RESUMEN
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate
#IMPORTACIONES DASHBOARD
import streamlit as st
import plotly.express as px

# URL base de la API de FastAPI
API_BASE_URL = "http://localhost:8000"


#---------------------------------------------------                    

#funcion para estilos de streamlit
def load_css(file_name):
    with open(file_name, "r") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
#--------------------------------
#función para login
def login(email: str):
    response = requests.post(f"{API_BASE_URL}/login", json={"email": email})
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error en el login: {response.json().get('detail', 'Error desconocido')}")
        return None
#--------------------------------
#función para obtener perfil
def obtener_perfil(email):
    try:
        response = requests.get(f"{API_BASE_URL}/perfil/{email}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        st.error(f"Error obteniendo perfil: {err}")
        return None
#--------------------------------
#mostrar perfil del alumno
def mostrar_perfil():
    # 🔹 Resetear la selección previa para evitar que se muestre debajo del perfil
    keys_to_clear = [
        "seleccion", "modulo_seleccionado", "modulo_id", 
        "unidad_seleccionada", "unidad_id", "resumen", 
        "resumen_pdf", "analysis", "current_response",
        "ayuda_seleccionada", "cv_analysis"
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    if 'email' in st.session_state:
        perfil = obtener_perfil(st.session_state['email'])  # Función externa
        if perfil:
            alumno = perfil.get("alumno", {})
            modulos_vertical = perfil.get("modulos_y_unidades_vertical", [])
            modulos_career = perfil.get("modulos_y_unidades_career", [])
            
            st.subheader("📌 Perfil del Alumno")
            st.write(f"**👤 Nombre**: {alumno.get('nombre', 'No disponible')}")
            st.write(f"**📧 Email**: {alumno.get('email', 'No disponible')}")
            st.write(f"**📚 Vertical**: {alumno.get('vertical', 'No disponible')}")
            st.write(f"**🎓 Career Readiness**: Career Readiness")
            
            # Mostrar módulos y unidades
            st.subheader("📂 Módulos y Unidades")
            for categoria, modulos in zip(["Vertical", "Career Readiness"], [modulos_vertical, modulos_career]):
                st.write(f"### {categoria}")
                for modulo in modulos:
                    with st.expander(f"📂 {modulo['nombre_modulo']}"):
                        for unidad in modulo["unidades"]:
                            st.write(f"- 📖 {unidad['nombre_unidad']}")
        else:
            st.warning("No se encontró el perfil.")
    st.stop()

#--------------------------------
# Función para obtener las opciones de vertical o career
def obtener_opciones(email: str):
    response = requests.post(f"{API_BASE_URL}/selecciona", json={"email": email})
    if response.status_code == 200:
        opciones = response.json()["opciones"]
        # Cambiar "Career" por "Career Readiness"
        return [opcion if opcion != "Career Readiness" else "Career Readiness" for opcion in opciones]
    else:
        st.error(f"Error al obtener opciones: {response.json().get('detail', 'Error desconocido')}")
        return None
#--------------------------------
# Función para obtener los módulos de una vertical
def obtener_modulos(vertical: str, email: str):
    # Cambiar "Career Readiness" a "Career" para la consulta SQL
    vertical_consulta = "Career Readiness" if vertical == "Career Readiness" else vertical
    response = requests.get(f"{API_BASE_URL}/modulos/{vertical_consulta}?email={email}")
    if response.status_code == 200:
        return response.json()["modulos"], response.json()["ids"]
    else:
        st.error(f"Error al obtener módulos: {response.json().get('detail', 'Error desconocido')}")
        return None, None
#--------------------------------
# Función para obtener las unidades de un módulo
def obtener_unidades(modulo: str):
    response = requests.get(f"{API_BASE_URL}/unidades/{modulo}")
    if response.status_code == 200:
        return response.json()["unidades"], response.json()["ids"]
    else:
        st.error(f"Error al obtener unidades: {response.json().get('detail', 'Error desconocido')}")
        return None, None
#--------------------------------
# Función para generar el resumen de una unidad
def generar_resumen(vertical: str, id_modulo: int, id_unidad: int):
    # Cambiar "Career Readiness" a "Career" para la consulta SQL
    vertical_consulta = "Career Readiness" if vertical == "Career Readiness" else vertical
    response = requests.post(
        f"{API_BASE_URL}/resumen/{vertical_consulta}",
        json={"id_modulo": id_modulo, "id_unidad": id_unidad}
    )
    if response.status_code == 200:
        return response.json()["resumen"]
    else:
        st.error(f"Error al generar el resumen: {response.json().get('detail', 'Error desconocido')}")
        return None

#---------------------------------------------------------------------
#FUNCIONES RESUMEN
#----------------------------------------------------
# Función para generar el PDF a partir de un texto

def generar_pdf(texto):
    buffer = BytesIO()
    
    # Configurar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    # Estilo con fuente estándar
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "Helvetica"  # Fuente estándar, no requiere archivo .ttf
    style.fontSize = 12
    style.leading = 14
    
    # Convertir saltos de línea
    texto_formateado = texto.replace('\n', '<br/>')
    
    # Crear y construir el PDF
    elementos = [Paragraph(texto_formateado, style)]
    doc.build(elementos)
    
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

#----------------------------------------------------------------------
# FUNCIONES AGENTES
#----------------------------------------------------------------------
#--------------------------------
# Función para obtener las ayudas
def obtener_ayudas(vertical: str):
    try:
        # Enviar vertical como query parameter
        response = requests.post(
            f"{API_BASE_URL}/selecciona_ayuda",
            params={"vertical": vertical}  # Query parameters
        )
        response.raise_for_status()
        return response.json()["opciones_ayuda"]
    except requests.exceptions.RequestException as err:
        st.error(f"Error al obtener las ayudas: {str(err)}")
        return None
#--------------------------------   
# Función para seleccionar la ayuda
def elegir_ayuda(id_sesion: int, request_data: dict, user_data: dict):
    try:
        response = requests.post(
            f"{API_BASE_URL}/ayuda",
            params={"id_sesion": id_sesion},  # Query parameter
            json={
                "request": request_data,  # Body
                "user": user_data  # Body
            }
        )
        response.raise_for_status()
        return response.json()["tipo_ayuda"]
    except requests.exceptions.RequestException as err:
        st.error(f"Error al elegir la ayuda: {str(err)}")
        return None
# ---------------------------------------
#Funcion para el sidebar
 # Reiniciar la aplicación
def sidebar_dynamic():
    with st.sidebar:
        # Botón de descarga resumen
        if st.session_state.get("resumen_pdf"):
            st.divider()
            st.markdown("### Descargas")
            st.download_button(
                label="📄 Descargar resumen",
                data=st.session_state.resumen_pdf,
                file_name=f"resumen_{st.session_state.id_sesion}.pdf",
                mime="application/pdf",
                key=f"resumen_pdf_{st.session_state.resumen_count}"
            )

def sidebar_dynamic_cv():
    with st.sidebar:
        # Botón de descarga análisis CV
        if st.session_state.get("analysis"):
            st.divider()
            st.download_button(
                label="📥 Descargar análisis CV",
                data=st.session_state.analysis,
                file_name=f"analisis_cv_{st.session_state.id_sesion}.txt",
                mime="text/plain",
                key=f"cv_analysis_{st.session_state.analysis_count}"
            )
#--------------------------------
#PUNTO DE UNIÓN ENTRE AGENTES Y ENDPOINTS

###QUERY ES LA CONSULAT Y MODULE MAP HAY QUE LLAMARLO EN EL APP
# Función para procesar la consulta


def process_query(query, module,module_map,help_type):
    if not query:
        return
    
    with st.spinner("Procesando tu consulta..."):
        try:
            if module == "Career Readiness":
                response = st.session_state.orchestrator.handle_request(query, module="both")
            else:
                # Usar el módulo seleccionado para la búsqueda
                if help_type == "Ejercicios prácticos":
                    response = st.session_state.orchestrator.ds_agents["practice"].create_exercise(query) if module == "Data Science" else st.session_state.orchestrator.fs_agents["practice"].create_exercise(query)
                else:
                    response = st.session_state.orchestrator.handle_request(query, module=module_map[module])
            
                return response
            st.success("¡Consulta procesada exitosamente!")
            # Forzar la recarga de la página para mostrar el contenido
            st.rerun()
            
        except Exception as e:
            st.error(f"Ocurrió un error al procesar tu consulta: {str(e)}")
            st.info("Por favor, intenta reformular tu pregunta o contacta al soporte técnico si el problema persiste.")

#--------------------------------
#despues de la pregunta concreta te da la solución
def toggle_solution():
    st.session_state.show_solution = not st.session_state.show_solution
#--------------------------------
#despues de la pregunta concreta te da la solución
def toggle_answer(i):
    if f'show_answer_{i}' not in st.session_state:
        st.session_state[f'show_answer_{i}'] = False
    st.session_state[f'show_answer_{i}'] = not st.session_state[f'show_answer_{i}']
#--------------------------------
#función para mostrar el contenido de los ejercicios prácticos y teoricos

def display_practice_content(content):
    try:
        # Dividir el contenido en secciones
        sections = {}
        current_section = ""
        current_content = []
        
        for line in content.split('\n'):
            line = line.strip()
            if "EJERCICIO PRÁCTICO:" in line:
                current_section = "ejercicio"
                current_content = []
            elif "PRUEBA DE CONOCIMIENTOS:" in line:
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "prueba"
                current_content = []
            elif "AUTOEVALUACIÓN:" in line:
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "evaluacion"
                current_content = []
            elif line:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # Crear pestañas
        tab1, tab2, tab3 = st.tabs(["📝 Ejercicio Práctico", "✍️ Prueba de Conocimientos", "📊 Autoevaluación"])
        
        # Pestaña de Ejercicio Práctico
        with tab1:
            if "ejercicio" in sections:
                st.markdown("### Ejercicio Práctico")
                ejercicio_content = sections["ejercicio"]
                partes = ejercicio_content.split("Solución:")
                
                if len(partes) > 0:
                    # Mostrar el enunciado
                    st.markdown(partes[0].strip())
                    
                    # Botón para mostrar/ocultar solución
                    if st.button("📝 Mostrar/Ocultar Solución", key="btn_solucion"):
                        st.session_state.show_solution = not st.session_state.get('show_solution', False)
                    
                    # Mostrar solución si está activada
                    if st.session_state.get('show_solution', False) and len(partes) > 1:
                        st.success("### Solución:")
                        solucion = partes[1].strip()
                        
                        # Detectar si hay código en la solución
                        lineas = solucion.split('\n')
                        codigo = []
                        explicacion = []
                        
                        en_bloque_codigo = False
                        for linea in lineas:
                            # Detectar si es una línea que parece código
                            es_codigo = any(keyword in linea for keyword in ['def ', 'class ', 'import ', 'return ', '    ', '=', 'if ', 'for ', 'while ']) or linea.strip().startswith(('(', '{', '[', '#'))
                            
                            if es_codigo:
                                if not en_bloque_codigo:
                                    # Si hay explicación pendiente, mostrarla
                                    if explicacion:
                                        st.markdown('\n'.join(explicacion))
                                        explicacion = []
                                    en_bloque_codigo = True
                                codigo.append(linea)
                            else:
                                if en_bloque_codigo:
                                    # Mostrar el bloque de código acumulado
                                    st.code('\n'.join(codigo), language='python')
                                    codigo = []
                                    en_bloque_codigo = False
                                explicacion.append(linea)
                        
                        # Mostrar cualquier contenido pendiente
                        if codigo:
                            st.code('\n'.join(codigo), language='python')
                        if explicacion:
                            st.markdown('\n'.join(explicacion))
        
        # Pestaña de Prueba de Conocimientos
        with tab2:
            if "prueba" in sections:
                st.markdown("### Prueba de Conocimientos")
                preguntas_raw = sections["prueba"].split("Pregunta")[1:]
                
                for i, pregunta_raw in enumerate(preguntas_raw, 1):
                    partes = pregunta_raw.split("Respuesta correcta:")
                    if len(partes) == 2:
                        pregunta = partes[0].strip()
                        respuesta = partes[1].strip()
                        
                        with st.container():
                            # Procesar el contenido de la pregunta
                            lineas = [l.strip() for l in pregunta.split('\n') if l.strip()]
                            
                            # Encontrar el enunciado
                            enunciado = ""
                            opciones = []
                            
                            for linea in lineas:
                                if linea.startswith(('A)', 'B)', 'C)', 'D)')):
                                    opciones.append(linea)
                                elif not enunciado and not linea.startswith(f"{i}:"):
                                    enunciado = linea
                            
                            # Mostrar la pregunta formateada
                            st.markdown(f"**Pregunta {i}:** {enunciado}")
                            
                            # Mostrar las opciones
                            for opcion in opciones:
                                st.markdown(f"- {opcion}")
                            
                            # Botón para mostrar/ocultar respuesta
                            if st.button(f"📝 Mostrar/Ocultar Solución Pregunta {i}", key=f"btn_pregunta_{i}"):
                                st.session_state[f'show_answer_{i}'] = not st.session_state.get(f'show_answer_{i}', False)
                            
                            if st.session_state.get(f'show_answer_{i}', False):
                                st.success(f"**Respuesta correcta:** {respuesta}")
                            
                            st.markdown("---")
        
        # Pestaña de Autoevaluación
        with tab3:
            if "evaluacion" in sections:
                st.markdown("### Autoevaluación")
                st.markdown(sections["evaluacion"])
                
    except Exception as e:
        st.error(f"Error al mostrar el contenido: {str(e)}")
#----------------------------------------------------------------------
#FUNCION CV
#----------------------------------------------------------------------
def analyze_cv(pdf_file):
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_path = tmp_file.name

        # Initialize Pinecone with environment variable
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        index_name = "cv-analysis"

        # Delete existing index if it exists
        try:
            pc.delete_index(index_name)
            st.info("Deleted existing index.")
        except Exception as e:
            st.info("No existing index to delete.")

        # Load PDF
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()

        # Split text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(pages)

        # Initialize embeddings with environment variable
        embeddings = MistralAIEmbeddings(
            model="mistral-embed",
            mistral_api_key=os.environ["MISTRAL_API_KEY"]
        )

        # Create new index
        if index_name not in pc.list_indexes().names():
            pc.create_index(
                name=index_name,
                dimension=1024,
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )

        # Get index
        index = pc.Index(index_name)

        # Create vector store
        vectorstore = LangchainPinecone.from_documents(
            documents=chunks,
            embedding=embeddings,
            index_name=index_name
        )

        # Query for analysis
        query = '''
        Como un experto en reclutar perfiles IT, con amplia experiencia en la mejora
        de la empleabilidad de perfiles recien llegados al sector. Tu mejor habilidad es analizar el contenido de
        los curriculum y proponer áreas de mejora. ¿Cuáles son las áreas de mejora de este curriculum?.
        '''

        # Retrieve context
        docs_pinecone = vectorstore.similarity_search_with_score(query, k=5)
        context_text = "\n\n".join([doc.page_content for doc, _score in docs_pinecone])

        # Prompt template
        PROMPT_TEMPLATE = """
        Contesta a la pregunta basándote sólo en el contexto:
        {context}
        Contesta a la pregunta basándote en el contexto: {question}.
        Provee una respuesta detallada.
        No justifiques tus respuestas.
        Habla de tú a tú con la persona del curriculum
        NO MENCIONES información que NO APAREZCA en el contexto.
        No digas cosas estilo "de acuerdo al contexto" o "como aparece en el contexto".
        Y RESPONDE EN ESPAÑOL.
        """

        # Format prompt
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=context_text, question=query)

        # Generate response using environment variable
        model = ChatMistralAI(
            mistral_api_key=os.environ["MISTRAL_API_KEY"],
            model_name="mistral-medium"
        )
        response_text = model.predict(prompt)

        # Clean up temporary file
        os.unlink(tmp_path)

        return response_text

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None
#----------------------------------------------------------------------
# FUNCIONES Dashboard (PROFESORES)
#----------------------------------------------------------------------
# Database connection function
def get_db_connection():
    return pymysql.connect(
        host='proyecto-db.cvmi428ogh5o.us-east-2.rds.amazonaws.com',
        user='admin',
        password='tripulaciones',
        database='proyecto_db',
        port=3306
    )
#--------------------------------
# Authentication function
def authenticate_teacher(email):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        query = """
        SELECT id_profesor, nombre, email 
        FROM claustro 
        WHERE email = %s
        """
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        
        if user:
            return {
                'id': user[0],
                'name': user[1],
                'email': user[2]
            }
        return None
    finally:
        conn.close()
#--------------------------------
# Function to get session data
def get_session_data(profesor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # First, verify the teacher exists and has bootcamps
        verify_query = """
        SELECT COUNT(*) 
        FROM p_clase 
        WHERE id_profesor = %s
        """
        cursor.execute(verify_query, (profesor_id,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            st.warning("No bootcamps found for this teacher")
            return pd.DataFrame()

        query = '''
        SELECT 
            COUNT(s.id_sesion) AS total_consultas,
            v.nombre AS vertical,
            CONCAT(v.nombre, '-', b.promocion, YEAR(b.f_comienzo)) AS bootcamp,
            m.nombre_modulo AS modulo,
            u.nombre_unidad AS unidad,
            DATE_FORMAT(s.login, '%%Y-%%m') AS mes
        FROM p_clase pc
        INNER JOIN bootcamp b ON pc.id_bootcamp = b.id_bootcamp
        INNER JOIN a_clase ac ON ac.id_bootcamp = pc.id_bootcamp
        INNER JOIN alumnos a ON a.id_alumno = ac.id_alumno
        INNER JOIN sesiones_dummy_2 s ON s.id_alumno = a.id_alumno
        INNER JOIN unidades u ON s.unidad_consulta = u.id_unidad
        INNER JOIN modulos m ON u.id_modulo = m.id_modulo
        INNER JOIN verticales v ON m.id_vertical = v.id_vertical
        WHERE pc.id_profesor = %s
        AND m.id_vertical = b.id_vertical
        GROUP BY mes, u.nombre_unidad, m.nombre_modulo, v.nombre, bootcamp
        '''
        
        # Execute query with cursor for better error handling
        cursor.execute(query, (profesor_id,))
        results = cursor.fetchall()
        
        # Convert results to DataFrame
        if results:
            columns = ['total_consultas', 'vertical', 'bootcamp', 'modulo', 'unidad', 'mes']
            df = pd.DataFrame(results, columns=columns)
            return df
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()
    finally:
        if 'conn' in locals():
            conn.close()
#--------------------------------


# Cargar CSS personalizado
def load_custom_css():
    st.markdown("""
        <style>
            /* Fondo en degradado */
            .stApp {
                background: linear-gradient(135deg, #b9252f, #be1e28, #960a16, #40060c);
                color: white;
                font-family: 'Arial', sans-serif;
            }

            /* Imagen en la esquina izquierda en la página de login */
            .login-logo {
                position: absolute;
                top: 10px;
                left: 10px;
                width: 100px;
                height: auto;
            }

            /* Imagen en la barra de menú en la página del dashboard */
            .sidebar-logo img {
                display: block;
                margin: 0 auto;
                width: 120px;
                height: auto;
            }

            /* Cabecera con borde blanco y botón de logout */
            .header-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background-color: black;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid white; /* Borde blanco */
            }

            .header-title {
                color: white;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Arial', sans-serif;
            }

            .logout-btn button {
                background-color: white !important;
                color: black !important;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px;
                border: 2px solid black !important;
                transition: all 0.3s ease;
            }

            .logout-btn button:hover {
                background-color: #f0f0f0 !important;
                transform: scale(1.05);
            }

            /* Ocultar subheader (rectángulo blanco) */
            .subheader {
                display: none;
            }

            /* Sidebar en negro */
            [data-testid="stSidebar"] {
                background-color: black !important;
                color: white !important;
            }

            /* Hacer gráficos de Plotly sin fondo */
            .stPlotlyChart {
                background: transparent !important;
            }

            /* Input de texto */
            .stTextInput input, .stTextArea textarea {
                font-family: 'Arial', sans-serif;
                color: black !important;
                background-color: white !important;
                border-radius: 10px;
                padding: 10px;
                border: 2px solid black;
            }
        </style>
    """, unsafe_allow_html=True)

# Cabecera con borde blanco y botón de logout
def display_header():
    st.markdown("""
        <div class="header-container">
            <div class="header-title">📊 Teacher Dashboard - {}</div>
            <div class="logout-btn">
                <form action="">
                    <button type="submit">Logout</button>
                </form>
            </div>
        </div>
    """.format(st.session_state.user['name']), unsafe_allow_html=True)

# Generar los gráficos
def generate_graphs(df):
    col1, col2, col3 = st.columns(3)

    # Gráfico de módulos más consultados
    with col1:
        module_data = df.groupby('modulo')['total_consultas'].sum().reset_index()
        fig_pie = px.pie(module_data, values='total_consultas', names='modulo', title='Módulos más consultados', hole=0.4)
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    # Gráfico de unidades más consultadas
    with col2:
        unit_data = df.groupby('unidad')['total_consultas'].sum().reset_index()
        unit_data = unit_data.sort_values('total_consultas', ascending=True)
        fig_bar = px.bar(unit_data, x='total_consultas', y='unidad', title='Unidades más consultadas', orientation='h')
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    # Gráfico de sesiones mensuales
    with col3:
        monthly_data = df.groupby('mes')['total_consultas'].sum().reset_index()
        fig_line = px.line(monthly_data, x='mes', y='total_consultas', title='Sesiones mensuales', markers=True)
        fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_line, use_container_width=True)
