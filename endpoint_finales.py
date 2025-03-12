from fastapi import FastAPI, Depends, HTTPException
#from app.models import User, Pregunta# crear tablas de modulo (?)
#from app.agents import agente_preguntas
#from app.rag import buscar_documento
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr #definir modelos de datos y validar entradas
from typing import List,Dict
from typing import Optional
import uvicorn
import pymysql #conectarse a la base de datos MySQL
from openai import OpenAI
import logging
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OpenAI_API_KEY ')
client = OpenAI(api_key=api_key)


def get_db():
    db = pymysql.connect(
        host= os.getenv('host'),
        user= os.getenv('user'),
        password=os.getenv('password'),
        database=os.getenv('database'),
        port=os.getenv('port'),
        cursorclass=pymysql.cursors.DictCursor
    )
    return db

app = FastAPI()

#Modelos Pydantic: Estos modelos definen la estructura de los datos que la API espera recibir o devolver
class Profesor(BaseModel):
    id_profesor: int
    nombre: str
    email: EmailStr
    bootcamp: str
class LoginResponseProf(BaseModel):
    message: str
    profesor: Profesor
class Alumno(BaseModel):#Esta clase nos da los datos del alumno de la query
    id_alumno: int
    nombre: str
    email: EmailStr
    vertical: str
    career: str

class LoginRequest(BaseModel):#login con email, (ponemos este comando para comprobar que es real el mail)
    email: EmailStr

class LoginResponse(BaseModel):#Comprueba si el alumno esta en la bd
    message: str
    id_sesion: int
    alumno: Optional[Alumno] = None#devuelve los datos del alumno si esta en la base d edatos y si no esta no da fallo, da felixivilidad


class SaludoResponse(BaseModel):#el modelo saluda al usuario
    mensaje: str

class PreguntaRequest(BaseModel):#el chat da opcion de career o modulo
    modulos: List[str]
    career: str

class SeleccionRequest(BaseModel):#lanza la pregunta el chat de selccion
    opcion: str
    id_sesion: int

class SeleccionResponse1(BaseModel):
    message: str
    opciones: List[str]

class SeleccionResponse(BaseModel):
    message: str
    unidad_consulta: str
    opciones: List[str]

class UnidadesResponse(BaseModel):#el modelo le da a elegir entre modulo o career
    mensaje: str
    unidades: List[str]  # Lista de unidades del módulo seleccionado
    ids: List[int]

class TemasResponse(BaseModel):#el modelo le da a elegir la unidad
    mensaje: str
    temas: List[str]
    ids: List[int]

class PreguntaRequest(BaseModel):#el modelo le dice si es teorica o practica
    mensaje: str
    tipo_pregunta: List[str]

class ResumenRequest(BaseModel):
    id_modulo: int
    id_unidad: int

class ResumenResponse(BaseModel):
    resumen: str

class ModulosResponse(BaseModel):
    message: str
    modulos: List[str]  # Lista de módulos de la vertical seleccionada
    ids: List[int]

class UserQueryRequest(BaseModel):
    vertical: str
    user_query: str

class TemaSeleccionado(BaseModel):
    id_alumno: int
    tema: str
# Definición de modelos
class Unidad(BaseModel):
    nombre_unidad: str
    id_unidad: int

class ModuloUnidades(BaseModel):
    nombre_modulo: str
    unidades: List[Unidad]

class PerfilResponse(BaseModel):
    alumno: Alumno
    modulos_y_unidades_vertical: List[ModuloUnidades]  # Módulos y unidades de la vertical del alumno
    modulos_y_unidades_career: List[ModuloUnidades]   # Módulos y unidades de Career

class AyudaRequest(BaseModel):
    opciones: dict
    

class AyudaResponse(BaseModel):
    # mensaje: str
    tipo_ayuda: str

class SeleccionAyudaRequest(BaseModel):
    opciones_ayuda: List[dict]

# Prompts específicos para cada vertical


def get_chat_response(vertical: str, user_query: str):
    PROMPTS ={
    'Data Science': """
    Eres un asistente docente especializado en el bootcamp de Data Science, que incluye estos módulos clave:
    1. Python Básico (Unidades: Variables y Tipos de Datos, Control de Flujo, Funciones y Módulos)
    2. Análisis de Datos (Unidades: Pandas Básico, Visualización de Datos, Análisis Estadístico)
    3. Machine Learning (Unidades: Introducción a ML, Modelos Supervisados, Modelos No Supervisados)

    Cuando un alumno formule una pregunta sobre una unidad específica:

    1. **Resumen Estructurado (150 palabras máx.):**
    - Objetivo principal de la unidad
    - 3 conceptos técnicos clave
    - Contexto dentro del módulo
    - Aplicación práctica con librerías principales (NumPy/Pandas/Scikit-learn)

    2. **Conexiones Curriculares:**
    - Relación con otras unidades del módulo (ej: Pandas Básico → base para Visualización)
    - Vinculación con otros módulos (ej: Python Básico → fundamento para Machine Learning)
    - Relevancia para el proyecto final del módulo (ej: Análisis Estadístico → validación de modelos)

    3. **Impacto Profesional:**
    - Contribución al proyecto final global de DS (ej: pipeline completo de datos)
    - Ejemplo real en sector tecnológico (ej: Pandas → análisis de datos en startups fintech)
    - Habilidad técnica certificable (ej: manipulación de datasets con Pandas)

    Usa analogías técnicas (ej: "DataFrames son como hojas de cálculo programables") 
    y mantén precisión en terminología técnica.
    """,

    'Full Stack': """
    Eres un asistente docente del bootcamp Full Stack con esta estructura:
    1. HTML/CSS (Unidades: HTML Estructura, CSS Estilos, Responsive Design)
    2. JavaScript (Unidades: JS Básico, DOM Manipulation, Eventos y Formularios)
    3. React (Unidades: Componentes React, Hooks y Estado, Routing y APIs)

    Al recibir una consulta sobre una unidad específica:

    1. **Resumen Técnico (120 palabras máx.):**
    - Propósito principal de la unidad
    - 3 tecnologías/librerías clave
    - Flujo de trabajo típico (ej: JS Básico → sintaxis → lógica → debugging)

    2. **Relaciones Técnicas:**
    - Dependencias con unidades anteriores (ej: HTML Estructura → base para Componentes React)
    - Integración con otros módulos (ej: DOM Manipulation → esencial para Hooks en React)
    - Rol en el proyecto final del módulo (ej: Routing y APIs → conexión backend-frontend)

    3. **Aplicación Real:**
    - Uso en el proyecto final global Full Stack (ej: Componentes React → UI dinámica)
    - Caso de industria (ej: Responsive Design → adaptación a dispositivos móviles en e-commerce)
    - Habilidad demandada en el mercado (ej: manejo de estado en aplicaciones complejas)

    Emplea ejemplos de código básico cuando sea relevante y enfatiza mejores prácticas de desarrollo.
    """,

    'Career Readiness': """
    Eres un asistente especializado en Career Readiness con esta estructura modular:
    1. Desarrollo Profesional (Unidades: Gestión de Carrera, Habilidades Blandas, Comunicación Efectiva)
    2. Búsqueda de Empleo (Unidades: CV y LinkedIn, Entrevistas, Portfolio Profesional)
    3. Networking y Marca Personal (Unidades: Networking Efectivo, Marca Personal Digital, Gestión de Redes)

    Al abordar una consulta sobre una unidad:

    1. **Contextualización Práctica (100 palabras máx.):**
    - Objetivo profesional clave
    - 3 estrategias concretas
    - Herramientas principales (ej: LinkedIn Premium para Networking Efectivo)

    2. **Interconexiones:**
    - Relación entre unidades (ej: CV y LinkedIn → base para Entrevistas)
    - Sinergia con otros módulos (ej: Comunicación Efectiva → útil en Networking)
    - Rol en el proyecto final del módulo (ej: Portfolio Profesional → showcase técnico)

    3. **Valor Laboral:**
    - Contribución al proyecto final global de Career (perfil profesional integrado)
    - Ejemplo de aplicación real (ej: Marca Personal Digital → atracción de reclutadores)
    - Métrica de éxito concreta (ej: optimización de CV → aumento tasa de respuestas)

    Usa lenguaje motivacional y ejemplos de casos reales de alumnos graduados.
    """
    }
    
    if vertical not in PROMPTS:
        raise ValueError("Vertical no válida. Usa: Data Science, Full Stack o Career Readiness.")
    
    completion = client.chat.completions.create(
        model="gpt-4-turbo",  # Modelo actualizado recomendado
        messages=[
            {
                "role": "system", 
                "content": PROMPTS[vertical]
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )
    return completion.choices[0].message.content



@app.get('/')
async def home():
    return "Bienvenido a la API del TA"

@app.get("/test-db")
def test_db():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        db.close()
        return {"message": "Conexión a la base de datos exitosa"}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/login_prof", response_model=LoginResponse)
def login_prof(request: LoginRequest):
    db = get_db()
    cursor = db.cursor()
    try:
        query_profesor = """
        SELECT id_profesor, nombre, email
        FROM claustro
        WHERE email = %s
        """
        
        cursor.execute(query_profesor, (request.email,))
        profesor_result = cursor.fetchone()
        # Obtener información del bootcamp 
        query_bootcamp_prof = """
        SELECT id_profesor,nombre
        FROM claustro c
        JOIN bootcamp b ON c.id_bootcamp = b.id_bootcamp
        WHERE c.id_profesor = %s
        LIMIT 1
        """
        
        cursor.execute(query_bootcamp_prof, (profesor_result['id_profesor'],))
        bootcamp_prof = cursor.fetchone()
        if not bootcamp_prof:
            raise HTTPException(status_code=400, detail="Profesor no asignado a ningún bootcamp")
        profesor = Profesor(
            id_profesor=profesor_result['id_profesor'],
            nombre=profesor_result['nombre'],
            email=profesor_result['email'],
            bootcamp=bootcamp_prof['nombre']
            
        )


        return LoginResponseProf(
            message="Inicio de sesión exitoso", 
            profesor=profesor
        )
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        db.close()

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Crear tabla sesiones si no existe
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sesiones (
            id_sesion INT AUTO_INCREMENT PRIMARY KEY,
            id_alumno INT NOT NULL,
            login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            unidad_consulta VARCHAR(255),
            FOREIGN KEY (id_alumno) REFERENCES alumnos(id_alumno)
        )
        """
        cursor.execute(create_table_query)
        db.commit()

        # Obtener información básica del alumno
        query_alumno = """
        SELECT id_alumno, nombre, email
        FROM alumnos
        WHERE email = %s
        """
        
        cursor.execute(query_alumno, (request.email,))
        alumno_result = cursor.fetchone()
        
        if not alumno_result:
            raise HTTPException(status_code=400, detail="Usuario no encontrado")
        
        # Obtener información del bootcamp y módulos del alumno
        query_bootcamp = """
        SELECT v.nombre as vertical
        FROM a_clase ac
        JOIN bootcamp b ON ac.id_bootcamp = b.id_bootcamp
        JOIN verticales v ON b.id_vertical = v.id_vertical
        WHERE ac.id_alumno = %s
        LIMIT 1
        """
        
        cursor.execute(query_bootcamp, (alumno_result['id_alumno'],))
        bootcamp_result = cursor.fetchone()
        
        if not bootcamp_result:
            raise HTTPException(status_code=400, detail="Alumno no asignado a ningún bootcamp")
        
        # Crear nueva sesión
        query_sesion = """
        INSERT INTO sesiones (id_alumno, login)
        VALUES (%s, CURRENT_TIMESTAMP)
        """
        
        cursor.execute(query_sesion, (alumno_result['id_alumno'],))
        
        db.commit()
        id_sesion = cursor.lastrowid
        
        # Crear objeto de respuesta con la información del alumno
        alumno = Alumno(
            id_alumno=alumno_result['id_alumno'],
            nombre=alumno_result['nombre'],
            email=alumno_result['email'],
            vertical=bootcamp_result['vertical'],
            career="Career Readiness"
        )
        
        return LoginResponse(
            message="Inicio de sesión exitoso", 
            id_sesion=id_sesion,
            alumno=alumno
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en el login: {str(e)}")
    finally:
        cursor.close()
        db.close()
#------------------------------

logging.basicConfig(level=logging.DEBUG)

@app.get("/perfil/{email}", response_model=PerfilResponse)
def obtener_perfil(email: str):
    db = get_db()
    cursor = db.cursor()

    try:
        # Obtener información básica del alumno
        query_alumno = """
        SELECT id_alumno, nombre, email
        FROM alumnos
        WHERE email = %s
        """
        cursor.execute(query_alumno, (email,))
        alumno_result = cursor.fetchone()

        if not alumno_result:
            raise HTTPException(status_code=404, detail="Alumno no encontrado")

        # Obtener la vertical del alumno
        query_bootcamp = """
        SELECT v.nombre AS vertical
        FROM a_clase ac
        JOIN bootcamp b ON ac.id_bootcamp = b.id_bootcamp
        JOIN verticales v ON b.id_vertical = v.id_vertical
        WHERE ac.id_alumno = %s
        LIMIT 1
        """
        cursor.execute(query_bootcamp, (alumno_result['id_alumno'],))
        bootcamp_result = cursor.fetchone()

        if not bootcamp_result:
            raise HTTPException(status_code=404, detail="Alumno no asignado a ningún bootcamp")

        # Obtener los módulos y unidades de la vertical del alumno
        vertical = bootcamp_result['vertical']
        modulos_y_unidades_vertical = obtener_modulos_y_unidades(vertical, cursor)

        # Obtener los módulos y unidades de Career
        modulos_y_unidades_career = obtener_modulos_y_unidades("Career Readiness", cursor)

        # Crear el objeto Alumno con la información recuperada
        alumno = Alumno(
            id_alumno=alumno_result['id_alumno'],
            nombre=alumno_result['nombre'],
            email=alumno_result['email'],
            vertical=vertical,
            career="Career Readiness"
        )

        # Devolver la respuesta con el nuevo modelo
        return {
            "alumno": alumno,
            "modulos_y_unidades_vertical": modulos_y_unidades_vertical,
            "modulos_y_unidades_career": modulos_y_unidades_career
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al obtener perfil: {str(e)}")
    finally:
        cursor.close()
        db.close()

# Función auxiliar para obtener módulos y unidades de una vertical
def obtener_modulos_y_unidades(vertical: str, cursor):
    # Obtener los módulos de la vertical
    query_modulos = """
    SELECT m.nombre_modulo, m.id_modulo
    FROM modulos m
    JOIN verticales v ON m.id_vertical = v.id_vertical
    WHERE v.nombre = %s
    """
    cursor.execute(query_modulos, (vertical,))
    modulos_result = cursor.fetchall()

    # Obtener las unidades para cada módulo
    modulos_y_unidades = []
    for modulo in modulos_result:
        query_unidades = """
        SELECT u.nombre_unidad, u.id_unidad
        FROM unidades u
        WHERE u.id_modulo = %s
        """
        cursor.execute(query_unidades, (modulo['id_modulo'],))
        unidades_result = cursor.fetchall()

        # Crear la lista de unidades para este módulo
        unidades = [
            {"nombre_unidad": unidad['nombre_unidad'], "id_unidad": unidad['id_unidad']}
            for unidad in unidades_result
        ]

        # Añadir el módulo y sus unidades a la lista
        modulos_y_unidades.append({
            "nombre_modulo": modulo['nombre_modulo'],
            "unidades": unidades
        })

    return modulos_y_unidades
#--------------------------------
#SAludo del chatbot
@app.get("/chatbot/greeting", response_model=SaludoResponse)
def get_chatbot_greeting():
    return {
        "mensaje": "¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?"
    }
#Career/modulo
@app.post("/selecciona", response_model=SeleccionResponse1)
def selecciona_modalidad(request: LoginRequest):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Obtener vertical específica del alumno
        query_vertical = """
        SELECT DISTINCT v.nombre as vertical
        FROM a_clase ac
        JOIN bootcamp b ON ac.id_bootcamp = b.id_bootcamp
        JOIN verticales v ON b.id_vertical = v.id_vertical
        WHERE ac.id_alumno = (
            SELECT id_alumno 
            FROM alumnos 
            WHERE email = %s
        )
        """
        cursor.execute(query_vertical, (request.email,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="No se encontró la vertical del alumno")
        
        # Las opciones siempre serán la vertical específica del alumno + Career
        opciones = [result['vertical'], 'Career Readiness']
        
        return SeleccionResponse1(
            message="Por favor, elige entre tu vertical específica o Career Readiness:",
            opciones=opciones
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cursor.close()
        db.close()


#el usuario seleciona y responde
import logging

logging.basicConfig(level=logging.DEBUG)

@app.post("/opcion", response_model=SeleccionResponse)
def seleccionar_opcion(request: SeleccionRequest, user: LoginRequest):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Fetch id_alumno
        query_alumno = """
        SELECT id_alumno
        FROM alumnos
        WHERE email = %s
        """
        cursor.execute(query_alumno, (user.email,))
        alumno_result = cursor.fetchone()
        
        if not alumno_result:
            raise HTTPException(status_code=400, detail="Usuario no encontrado")
        
        # Fetch valid options
        query_opciones = """
        SELECT m.nombre_modulo, v.nombre as vertical
        FROM a_clase ac
        JOIN bootcamp b ON ac.id_bootcamp = b.id_bootcamp
        JOIN modulos m ON b.id_vertical = m.id_vertical
        JOIN verticales v ON b.id_vertical = v.id_vertical
        WHERE ac.id_alumno = %s
        """
        cursor.execute(query_opciones, (alumno_result['id_alumno'],))
        results = cursor.fetchall()
        
        if not results:
            raise HTTPException(status_code=400, detail="No se encontraron opciones para este alumno")
        
        opciones_validas = [row['nombre_modulo'] for row in results] + [row['vertical'] for row in results]
        
        if request.opcion not in opciones_validas:
            raise HTTPException(status_code=400, detail="Opción no válida")
        
        # Validate session
        query_sesion = """
        SELECT s.id_sesion, a.email
        FROM sesiones s
        JOIN alumnos a ON s.id_alumno = a.id_alumno
        WHERE s.id_sesion = %s AND a.email = %s
        """
        cursor.execute(query_sesion, (request.id_sesion, user.email))
        sesion_result = cursor.fetchone()
        
        if not sesion_result:
            raise HTTPException(status_code=400, detail="Sesión no válida")
        
        # Update session
        query_update_sesion = """
        UPDATE sesiones 
        SET unidad_consulta = %s
        WHERE id_sesion = %s
        """
        cursor.execute(query_update_sesion, (request.opcion, request.id_sesion))
        db.commit()
        
        # Return response with opciones
        return SeleccionResponse(
            message=f"Has seleccionado la opción: {request.opcion}",
            unidad_consulta=request.opcion,
            opciones=opciones_validas  # Include the valid options
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al procesar la opción: {str(e)}")
    finally:
        cursor.close()
        db.close()

@app.get("/modulos/{vertical}", response_model=ModulosResponse)
def obtener_modulos(vertical: str, email: str):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Verificar que el alumno tenga acceso a esta vertical
        if vertical != 'Career Readiness':
            query_verificacion = """
            SELECT 1
            FROM a_clase ac
            JOIN bootcamp b ON ac.id_bootcamp = b.id_bootcamp
            JOIN verticales v ON b.id_vertical = v.id_vertical
            WHERE ac.id_alumno = (
                SELECT id_alumno 
                FROM alumnos 
                WHERE email = %s
            )
            AND v.nombre = %s
            """
            cursor.execute(query_verificacion, (email, vertical))
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="No tienes acceso a esta vertical")
        else:
            vertical = "Career Readiness"
            
        # Obtener módulos de la vertical seleccionada
        query_modulos = """
        SELECT m.nombre_modulo, m.id_modulo
        FROM modulos m
        JOIN verticales v ON m.id_vertical = v.id_vertical
        WHERE v.nombre = %s
        ORDER BY m.id_modulo
        """
        cursor.execute(query_modulos, (vertical,))
        modulos = cursor.fetchall()
        
        if not modulos:
            raise HTTPException(status_code=404, detail="No se encontraron módulos")
        
        return ModulosResponse(
            message=f"Módulos disponibles en {vertical}:",
            modulos=[modulo['nombre_modulo'] for modulo in modulos],
            ids=[modulo['id_modulo'] for modulo in modulos]
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cursor.close()
        db.close()




# Endpoint para obtener unidades de un módulo
@app.get("/unidades/{modulo}", response_model=UnidadesResponse)
def obtener_unidades(modulo: str):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Obtener unidades del módulo seleccionado
        query_unidades = """
        SELECT u.nombre_unidad, u.id_unidad
        FROM unidades u
        JOIN modulos m ON u.id_modulo = m.id_modulo
        WHERE m.nombre_modulo = %s
        ORDER BY u.id_unidad
        """
        cursor.execute(query_unidades, (modulo,))
        unidades = cursor.fetchall()
        
        if not unidades:
            raise HTTPException(status_code=404, detail="No se encontraron unidades para este módulo")
        
        return UnidadesResponse(
            mensaje=f"Unidades disponibles en el módulo {modulo}:",
            unidades=[unidad['nombre_unidad'] for unidad in unidades],
            ids=[unidad['id_unidad'] for unidad in unidades]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cursor.close()
        db.close()



@app.post("/temas/{id_unidad}/seleccionar")
def seleccionar_tema(id_unidad: int, tema_seleccionado: TemaSeleccionado):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Verificar que el tema seleccionado pertenezca a la unidad
        query_verificar_tema = """
        SELECT nombre_unidad as tema, id_unidad as id
        FROM unidades
        WHERE id_unidad = %s AND nombre_unidad = %s
        """
        cursor.execute(query_verificar_tema, (id_unidad, tema_seleccionado.tema))
        tema_valido = cursor.fetchone()
        
        if not tema_valido:
            raise HTTPException(status_code=404, detail="El tema seleccionado no es válido para esta unidad")
        
        # Registrar la selección del alumno en la tabla sesiones
        insert_query = """
        INSERT INTO sesiones (id_alumno,unidad_consulta)
        VALUES (%s,%s)
        """
        cursor.execute(insert_query, (tema_seleccionado.id_alumno,tema_seleccionado.tema))
        db.commit()
        
        return {"mensaje": f"Tema '{tema_seleccionado.tema}' seleccionado y registrado correctamente"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cursor.close()
        db.close()
#---------------------------------------------
import logging

logging.basicConfig(level=logging.DEBUG)
import mysql.connector


@app.post("/resumen/{vertical}", response_model=ResumenResponse)
def generar_resumen_unidad(vertical: str, request: ResumenRequest):
    db = get_db()
    cursor = db.cursor()
    
    try:
        logging.debug("Iniciando generación de resumen...")
        
        # 1. Obtener metadatos de la unidad
        query = """
        SELECT 
            m.nombre_modulo,
            u.nombre_unidad,
            v.nombre AS vertical
        FROM modulos m
        JOIN unidades u ON m.id_modulo = u.id_modulo
        JOIN verticales v ON m.id_vertical = v.id_vertical
        WHERE m.id_modulo = %s AND u.id_unidad = %s
        """
        cursor.execute(query, (request.id_modulo, request.id_unidad))
        result = cursor.fetchone()
        logging.debug(f"Resultado de la consulta: {result}")
        
        if not result:
            raise HTTPException(status_code=404, detail="Recurso no encontrado")
        
        # 2. Validar coincidencia de vertical
        if result['vertical'].upper() != vertical.upper():
            raise HTTPException(
                status_code=400,
                detail=f"Vertical del módulo ({result['vertical']}) no coincide con {vertical}"
            )
        
        # 3. Construir prompt contextualizado
        prompt_unidad = f"""
        Por favor genera un análisis completo para la unidad '{result['nombre_unidad']}'
        del módulo '{result['nombre_modulo']}' siguiendo tu estructura estándar:
        """
        logging.debug(f"Prompt generado: {prompt_unidad}")
        
        # 4. Obtener respuesta usando tus prompts existentes
        resumen = get_chat_response(
            vertical=vertical,
            user_query=prompt_unidad
        )
        logging.debug(f"Resumen generado: {resumen}")
        
        return {"resumen": resumen}
        
    except ValueError as ve:
        logging.error(f"Error de validación: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he:
        logging.error(f"Error HTTP: {str(he)}")
        raise he
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cursor.close()
        db.close()

#----------------------------------------------------------------------
#endpoint para la seleccion de ayuda


@app.post("/selecciona_ayuda", response_model=SeleccionAyudaRequest)
def selecciona_ayuda(vertical: str):
    db = get_db()
    cursor = db.cursor()
    
    try:
        
        # Las opciones siempre serán la vertical específica del alumno + Career
        if vertical == "Career Readiness":
         
            query_ayuda = """
            SELECT tipo_ayuda
            FROM ayuda 
            WHERE id_ayuda in (5,6)
            """
            cursor.execute(query_ayuda)
            result = cursor.fetchall()
            return SeleccionAyudaRequest(
                message="Por favor, elige entre las ayudas:",
                opciones_ayuda=result
            )
        elif vertical == "Data Science" or vertical == "Full Stack":
            query_ayuda = """
            SELECT tipo_ayuda
            FROM ayuda 
            WHERE id_ayuda in (1,2,3,4)
            """
            cursor.execute(query_ayuda)
            result = cursor.fetchall()
        
            return SeleccionAyudaRequest(
                message="Por favor, elige entre las ayudas:",
                opciones_ayuda=result
            )
        else:
            raise HTTPException(status_code=404, detail="No se encontró la vertical del alumno")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cursor.close()
        db.close()

    

@app.post("/ayuda", response_model=AyudaResponse)
def elige_ayuda(request:AyudaRequest, user: LoginRequest,id_sesion: int):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Fetch id_alumno
        query_alumno = """
        SELECT id_alumno
        FROM alumnos
        WHERE email = %s
        """
        cursor.execute(query_alumno, (user.email,))
        alumno_result = cursor.fetchone()
        
        if not alumno_result:
            raise HTTPException(status_code=400, detail="Usuario no encontrado")
        
        
        # Fetch valid options
        query_opciones = """
        SELECT tipo_ayuda
        FROM ayuda 
        JOIN sesiones ON ayuda.id_ayuda = sesiones.id_ayuda
        WHERE id_sesion = %s
        """
        cursor.execute(query_opciones, (id_sesion,))
        results = cursor.fetchone()
        
        #Update session
        # query_update_ayuda = """
        # UPDATE sesiones 
        # SET tipo_ayuda = %s
        # WHERE id_ayuda = %s
        # """
        # cursor.execute(query_update_ayuda, (request.opciones))
        # db.commit()
        tipo_ayuda = request.opciones["tipo_ayuda"]
        # Return response with opciones
        return AyudaResponse(
            # mensaje=f"Has seleccionado la opción: {request.tipo_ayuda}",
            tipo_ayuda=tipo_ayuda
            
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al procesar la opción: {str(e)}")
    finally:
        cursor.close()
        db.close()


