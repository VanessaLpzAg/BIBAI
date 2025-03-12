import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Literal
from pinecone import Pinecone
from langchain.chat_models import ChatOpenAI
from serpapi import GoogleSearch
from mistralai.client import MistralClient
import asyncio

# Cargar variables de entorno desde .env
load_dotenv()

# Verificar que las variables requeridas existen
required_vars = [
    "PINECONE_API_KEY",
    "environment_pinecone",
    "index_name_pinecone_ds",
    "index_name_pinecone_fs",
    "index_name_pinecone_pdf",
    "MISTRAL_API_KEY",
    "OpenAI_API_KEY",
    "SerpAPI_KEY"
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Faltan las siguientes variables de entorno en el archivo .env:\n" + "\n".join(missing_vars))

def embed_text(text: str):
    try:
        client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))
        embeddings = client.embeddings(
            model="mistral-embed",
            input=[text]
        )
        return embeddings.data[0].embedding
    except Exception as e:
        print(f"Error al generar embeddings: {str(e)}")
        return None

class PineconeRetriever:
    def __init__(self, api_key: str, environment: str, ds_index_name: str, fs_index_name: str, pdf_index_name: str):
        if not all([api_key, environment, ds_index_name, fs_index_name, pdf_index_name]):
            raise ValueError("Faltan parámetros requeridos para inicializar PineconeRetriever")
        
        # Inicializar Pinecone
        self.pc = Pinecone(api_key=api_key)
        # Índice para Data Science
        self.ds_index = self.pc.Index(ds_index_name)
        # Índice para Full Stack
        self.fs_index = self.pc.Index(fs_index_name)
        # Índice para PDFs
        self.pdf_index = self.pc.Index(pdf_index_name)

    def search_documents(self, query: str, module: Literal["ds", "fs"] = "ds", top_k: int = 5) -> str:
        query_vector = embed_text(query)
        if query_vector is None:
            return "Lo siento, hubo un error al procesar tu consulta. Por favor, inténtalo de nuevo."
        
        try:
            # Seleccionar el índice según el módulo
            index = self.ds_index if module == "ds" else self.fs_index
            
            # Buscar en el índice específico del módulo
            results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
            module_docs = [match.metadata['text'] for match in results.matches]
            
            # Buscar en el índice de PDFs
            pdf_results = self.pdf_index.query(vector=query_vector, top_k=top_k, include_metadata=True)
            pdf_docs = [f"[PDF] {match.metadata['text']}" for match in pdf_results.matches]
            
            # Combinar y ordenar resultados
            all_docs = []
            for i in range(max(len(module_docs), len(pdf_docs))):
                if i < len(module_docs):
                    all_docs.append(module_docs[i])
                if i < len(pdf_docs):
                    all_docs.append(pdf_docs[i])
            
            return "\n\n".join(all_docs)
        except Exception as e:
            print(f"Error al buscar en Pinecone: {str(e)}")
            return "Lo siento, hubo un error al buscar documentos relevantes. Por favor, inténtalo de nuevo."

    def search_both_modules(self, query: str, top_k: int = 5) -> str:
        query_vector = embed_text(query)
        if query_vector is None:
            return "Lo siento, hubo un error al procesar tu consulta. Por favor, inténtalo de nuevo."
        
        try:
            # Buscar en ambos índices de módulos
            ds_results = self.ds_index.query(vector=query_vector, top_k=top_k, include_metadata=True)
            fs_results = self.fs_index.query(vector=query_vector, top_k=top_k, include_metadata=True)
            
            # Buscar en el índice de PDFs
            pdf_results = self.pdf_index.query(vector=query_vector, top_k=top_k, include_metadata=True)
            
            # Combinar resultados
            ds_docs = [f"[Data Science] {match.metadata['text']}" for match in ds_results.matches]
            fs_docs = [f"[Full Stack] {match.metadata['text']}" for match in fs_results.matches]
            pdf_docs = [f"[PDF] {match.metadata['text']}" for match in pdf_results.matches]
            
            # Intercalar resultados de los tres índices
            combined_docs = []
            for i in range(max(len(ds_docs), len(fs_docs), len(pdf_docs))):
                if i < len(ds_docs):
                    combined_docs.append(ds_docs[i])
                if i < len(fs_docs):
                    combined_docs.append(fs_docs[i])
                if i < len(pdf_docs):
                    combined_docs.append(pdf_docs[i])
            
            return "\n\n".join(combined_docs)
        except Exception as e:
            print(f"Error al buscar en los índices de Pinecone: {str(e)}")
            return "Lo siento, hubo un error al buscar en los índices. Por favor, inténtalo de nuevo."

class ResearchAgent:
    def __init__(self, llm: ChatOpenAI, module: Literal["ds", "fs"]):
        self.llm = llm
        self.module = module
        self.w3schools_base_url = "https://www.w3schools.com"

        if not os.getenv("SerpAPI_KEY"):
            raise ValueError("SerpAPI_KEY no está configurado en el archivo .env")

    def google_search(self, query: str) -> List[Dict[str, str]]:
        params = {
            "q": query,
            "api_key": os.getenv("SerpAPI_KEY")
        }
        search = GoogleSearch(params)
        results = search.get_dict().get("organic_results", [])
        return [{"title": res["title"], "link": res["link"]} for res in results]

    def get_w3schools_content(self, query: str) -> List[Dict[str, str]]:
        try:
            search_url = f"{self.w3schools_base_url}/search/search.asp?q={query}"
            response = requests.get(search_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for result in soup.find_all('div', class_='w3-col l8 m12'):
                title = result.find('h2')
                if title:
                    results.append({
                        'title': title.text,
                        'url': self.w3schools_base_url + title.find('a')['href'] if title.find('a') else None
                    })
            return results
        except Exception as e:
            print(f"Error al buscar en W3Schools: {str(e)}")
            return []

    def research(self, query: str) -> str:
        # Modificar la consulta según el módulo
        module_context = "Data Science" if self.module == "ds" else "Full Stack Development"
        enhanced_query = f"{query} en el contexto de {module_context}"
        
        search_results = self.google_search(enhanced_query)
        search_context = "\n".join([f"- {res['title']}: {res['link']}" for res in search_results])
        
        w3schools_results = self.get_w3schools_content(query)
        w3schools_context = "\n".join([f"- {result['title']}: {result['url']}" for result in w3schools_results])

        research_prompt = f"""
        Eres un asistente de investigación experto para estudiantes de bootcamp de {module_context}, en todas las consultas del estudiante facilita enlaces de diferentes
        webs en relación a su consulta.
        El estudiante está preguntando sobre:
        {query}

        Usando la siguiente información de varias fuentes, proporciona una investigación completa
        específicamente enfocada en {module_context}, con la presencia de enlaces relacionados a diferentes webs:

        Resultados de búsqueda en Google:   
        {search_context}

        W3Schools Resources:
        {w3schools_context}

        Por favor, proporciona:
        1. Conceptos clave y definiciones relevantes para {module_context}
        2. Mejores prácticas y estándares en el contexto de {module_context}
        3. Enlaces a tutoriales y ejemplos relevantes de W3Schools
        4. Casos de uso comunes en {module_context}
        5. Recursos adicionales y referencias específicos para {module_context}
        

        Responde en español y en todas las respuestas muestra dos enlaces de web o tutoriales.
        """
        return self.llm.invoke(research_prompt).content

class SummarizeAgent:
    def __init__(self, llm: ChatOpenAI, module: str):
        self.llm = llm
        self.module = module

    def summarize(self, content: str) -> str:
        summarize_prompt = f"""
        Eres un experto en crear resúmenes claros y concisos para estudiantes de bootcamp de {self.module}.
        El estudiante necesita un resumen de:
        {content}

        Por favor proporciona:

        1. Una visión general breve específica para {self.module}
        2. Puntos clave y conceptos relevantes en {self.module}
        3. Relaciones importantes entre los conceptos en el contexto de {self.module}
        4. Aplicaciones prácticas en el campo de {self.module}

        Responde en español.

        RESUMEN:
        """
        return self.llm.invoke(summarize_prompt).content

class StudySupportAgent:
    def __init__(self, llm: ChatOpenAI, module: str):
        self.llm = llm
        self.module = module

    def explain(self, query: str) -> str:
        support_prompt = f"""
        Eres un tutor experto ayudando a estudiantes de bootcamp de {self.module} a entender conceptos complejos.
        El estudiante tiene esta pregunta:
        {query}

        Por favor, proporciona:

        1. Explicación clara del concepto en el contexto de {self.module}
        2. Desglose paso a paso de los temas complejos
        3. Conceptos erróneos comunes en {self.module} y cómo evitarlos
        4. Consejos para una mejor comprensión específicos para {self.module}

        Responde en español.

        EXPLICACIÓN:
        """
        return self.llm.invoke(support_prompt).content

class PracticeAgent:
    def __init__(self, llm: ChatOpenAI, module: str):
        self.llm = llm
        self.module = module

    def create_exercise(self, topic: str) -> str:
        practice_prompt = f"""
        Eres un instructor experto creando ejercicios prácticos para estudiantes de bootcamp de {self.module}.
        El estudiante quiere practicar sobre: {topic}

        Genera un ejercicio completo siguiendo EXACTAMENTE este formato:

        EJERCICIO PRÁCTICO:
        [Escribe aquí el enunciado del ejercicio de manera clara y detallada]

        Solución:
        [Escribe aquí la solución completa y detallada]

        PRUEBA DE CONOCIMIENTOS:
        Pregunta 1:
        [Escribe aquí el enunciado de la pregunta]
        A) [Opción A]
        B) [Opción B]
        C) [Opción C]
        D) [Opción D]
        Respuesta correcta: [Letra] - [Explicación detallada]

        Pregunta 2:
        [Escribe aquí el enunciado de la pregunta]
        A) [Opción A]
        B) [Opción B]
        C) [Opción C]
        D) [Opción D]
        Respuesta correcta: [Letra] - [Explicación detallada]

        Pregunta 3:
        [Escribe aquí el enunciado de la pregunta]
        A) [Opción A]
        B) [Opción B]
        C) [Opción C]
        D) [Opción D]
        Respuesta correcta: [Letra] - [Explicación detallada]

        Pregunta 4:
        [Escribe aquí el enunciado de la pregunta]
        A) [Opción A]
        B) [Opción B]
        C) [Opción C]
        D) [Opción D]
        Respuesta correcta: [Letra] - [Explicación detallada]

        Pregunta 5:
        [Escribe aquí el enunciado de la pregunta]
        A) [Opción A]
        B) [Opción B]
        C) [Opción C]
        D) [Opción D]
        Respuesta correcta: [Letra] - [Explicación detallada]

        AUTOEVALUACIÓN:
        - Criterios de evaluación:
          [Lista de criterios específicos]
        
        - Áreas de mejora:
          [Sugerencias de mejora]
        
        - Recursos adicionales:
          [Enlaces y recursos relevantes]

        Es EXTREMADAMENTE importante que:
        1. Mantengas EXACTAMENTE los títulos y el formato mostrado
        2. Incluyas "Solución:" como separador en el ejercicio práctico
        3. Numeres las preguntas exactamente como se muestra
        4. Incluyas "Respuesta correcta:" antes de cada respuesta
        5. El contenido sea específico para {self.module}
        6. Todo esté en español
        """
        return self.llm.invoke(practice_prompt).content

class JobPrepAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def provide_guidance(self, query: str) -> str:
        job_prep_prompt = f"""
        Eres un experto chatbot asistiendo a estudiantes de bootcamp con la preparación para el trabajo, brindándoles orientación sobre cómo crear su currículum, mantener un perfil de LinkedIn actualizado, buscar empleo y prepararse para entrevistas.

        El estudiante está preguntando lo siguiente:
        {query}

        Eres un experto chatbot asistiendo a estudiantes de bootcamp que están en transición de los estudios al mercado laboral. El estudiante está ahora preparándose para entrar al mundo laboral y necesita orientación práctica sobre cómo navegar este proceso de manera efectiva. El estudiante tiene poca o ninguna experiencia laboral y debe enfocarse en resaltar habilidades transferibles, construir un currículum sólido, crear un perfil de LinkedIn impactante y buscar empleos de manera efectiva. Además, el estudiante necesita ayuda para prepararse para entrevistas, comprender qué buscan los empleadores y practicar preguntas comunes de entrevistas.

        Por favor, proporciona consejos prácticos y aplicables adaptados a un recién graduado que busca construir una carrera y conseguir su primer empleo. Los consejos deben incluir:
            1. Consejos para crear un currículum atractivo que resalte habilidades y educación relevantes, basado en el currículum del alumno que adjuntara.
            2. Pasos para optimizar un perfil de LinkedIn para la búsqueda de empleo y la creación de redes.
            3. Orientación sobre cómo buscar empleo de manera efectiva a través de LinkedIn y otras plataformas.
            4. Consejos prácticos sobre cómo prepararse para entrevistas, incluyendo cómo responder a preguntas comunes y cómo causar una impresión positiva.

        **Responde en español.**

        AYUDA PARA PREPARACIÓN DE EMPLEO:
        """
        return self.llm.invoke(job_prep_prompt).content

class StudyOrchestrator:
    def __init__(self, llm: ChatOpenAI):
        # Verificar que tenemos la clave de OpenAI
        if not os.getenv("OpenAI_API_KEY"):
            raise ValueError("OpenAI_API_KEY no está configurado en el archivo .env")
        
        # Crear agentes específicos para cada módulo
        self.ds_agents = {
            "research": ResearchAgent(llm, "ds"),
            "summarize": SummarizeAgent(llm, "Data Science"),
            "support": StudySupportAgent(llm, "Data Science"),
            "practice": PracticeAgent(llm, "Data Science")
        }
        
        self.fs_agents = {
            "research": ResearchAgent(llm, "fs"),
            "summarize": SummarizeAgent(llm, "Full Stack"),
            "support": StudySupportAgent(llm, "Full Stack"),
            "practice": PracticeAgent(llm, "Full Stack")
        }
        
        # JobPrepAgent es común para ambos módulos
        self.job_prep_agent = JobPrepAgent(llm)

        # Inicializar el recuperador de Pinecone usando variables de entorno
        self.pinecone_retriever = PineconeRetriever(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("environment_pinecone"),
            ds_index_name=os.getenv("index_name_pinecone_ds"),
            fs_index_name=os.getenv("index_name_pinecone_fs"),
            pdf_index_name=os.getenv("index_name_pinecone_pdf")
        )

    def handle_request(self, query: str, module: Literal["ds", "fs", "both"] = "both") -> str:
        # Si es una consulta de trabajo, usar el agente común
        if any(keyword in query.lower() for keyword in ["trabajo", "job", "career", "entrevista", "cv", "linkedin"]):
            return self.job_prep_agent.provide_guidance(query)

        # Para otras consultas, usar el agente específico del módulo
        agents = self.ds_agents if module == "ds" else self.fs_agents

        if "research" in query or "search" in query or "find" in query or "enlaces" in query or "link" in query:
            return agents["research"].research(query)
        elif "summarize" in query or "summary" in query or "resume" in query:
            return agents["summarize"].summarize(query)
        elif "practice" in query or "exercise" in query or "example" in query:
            return agents["practice"].create_exercise(query)
        else:
            # Usar Pinecone según el módulo seleccionado
            if module == "both":
                doc_context = self.pinecone_retriever.search_both_modules(query)
            else:
                doc_context = self.pinecone_retriever.search_documents(query, module=module)
            
            consulta_con_contexto = f"{query}\n\nInformación extraída de documentos:\n{doc_context}"
            return agents["support"].explain(consulta_con_contexto) 