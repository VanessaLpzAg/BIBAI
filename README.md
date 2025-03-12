# BIBAI: Asistente de IA para Estudiantes 🎓🤖

Bienvenido a BIBAI, un asistente de inteligencia artificial diseñado para apoyar a los estudiantes del bootcamp The Bridge. Este chatbot interactivo te ayudará durante tu proceso de aprendizaje, ofreciéndote resúmenes de temas, análisis de CV, respuestas a tus dudas y más. ¡Todo lo que necesitas para tener éxito en tu carrera está aquí! 🚀

## Funcionalidades principales ✨

### 1. Inicio de sesión con email 📧

Los estudiantes pueden iniciar sesión utilizando su correo electrónico.
Una vez autenticado, el estudiante verá su perfil y podrá acceder a los recursos disponibles.

### 2. Selección de curso y módulo 📚

Después de iniciar sesión, los estudiantes pueden elegir su vertical/career (por ejemplo: Data Science, Full Stack, etc.).
Luego, pueden elegir un módulo específico y un tema para profundizar en su aprendizaje.

### 3. Generación de resúmenes de temas 📝

Los estudiantes pueden generar resúmenes de los temas seleccionados para obtener un repaso rápido.
Estos resúmenes pueden descargarse en formato PDF para tenerlos disponibles offline.

### 4. Ayuda personalizada 💡

El asistente ofrece varias ayudas personalizadas dependiendo de las necesidades del estudiante:

- Ejercicios prácticos: Desafíos interactivos para aplicar los conocimientos adquiridos.

- Análisis de CV: Subir el CV y obtener una análisis detallado sobre cómo mejorarlo.

- Ayuda general: Respuestas a dudas comunes y ayuda sobre temas relacionados con el curso.

### 5. Interacción de Chat 💬

Los estudiantes pueden hacer preguntas directamente al asistente sobre temas de su curso.

El chatbot responde utilizando los modelos de IA de OpenAI para proporcionar respuestas claras y detalladas.


----------------------------------------------------------------------------------------------------------- 

## Cómo instalar y usar 📥

### 1. Clonar el repositorio 🚀

Para empezar, clona este repositorio en tu máquina local:

```bash
git clone https://github.com/VanessaLpzAg/BIBAI.git
```

### 2. Instalar dependencias 📦

Necesitarás Python 3.x para ejecutar la aplicación. Asegúrate de tener todas las dependencias necesarias:

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno 🔑

Crea un archivo .env y añade tus claves API de los servicios que se utilizan en la aplicación:

```bash
PINECONE_API_KEY=tu_clave_pinecone
MISTRAL_API_KEY=tu_clave_mistral
OpenAI_API_KEY=tu_clave_openai
``` 

### 4. Ejecutar la aplicación 🖥️

Para correr la aplicación de forma local, usa:

```bash
streamlit run app.py
```

### 5. Acceder al chat 💬

Abre tu navegador y ve a http://localhost:8501 para empezar a interactuar con el asistente.

-----------------------------------------------------------------------------------

## Flujo de la Aplicación ⚙️

- Inicio de sesión: Los estudiantes se autentican con su correo electrónico.

- Selección de vertical y módulo: Eligen su especialización y tema a estudiar.

- Generación de resúmenes: Pueden generar resúmenes en formato PDF de los temas seleccionados.

- Ayuda personalizada: Los estudiantes reciben ayuda sobre ejercicios, análisis de CV o dudas generales.

- Chat interactivo: El chatbot proporciona respuestas personalizadas a las preguntas del estudiante.

---------------------------------------------------------------------------------- 

## Tecnologías utilizadas. ⚡

🔹 Lenguajes de Programación.

- Python → Desarrollo de backend y lógica del chatbot.


🔹 Frameworks y Librerías.

- FastAPI → Creación de la API web rápida y eficiente.

- LangChain → Orquestación de modelos de lenguaje (LLMs) y generación de respuestas.

- NumPy & Pandas → Procesamiento y análisis de datos.

- OpenAI API → Uso de modelos avanzados de lenguaje como GPT-4.


🔹 Base de Datos y Almacenamiento.

- Pinecone → Almacenamiento de vectores para realizar búsquedas semánticas rápidas y eficientes.

- Mistral AI → Uso de embeddings y procesamiento de lenguaje natural avanzado para mejorar la búsqueda y generación de respuestas en tiempo real.

- MySQL → Base de datos relacional para almacenar interacciones, perfiles de usuarios y configuraciones del sistema.

- AWS → Infraestructura en la nube que proporciona servicios de almacenamiento (S3), bases de datos (RDS) y despliegue escalable para la aplicación.


🔹 Interfaz de Usuario.

- Streamlit → Desarrollo rápido de una interfaz interactiva para pruebas y visualización.


🔹 Despliegue.

- Docker → Contenerización de la aplicación, facilitando su portabilidad y ejecución en cualquier entorno.

- Google Cloud Run → Plataforma serverless para desplegar y escalar automáticamente los contenedores de BibAI según la demanda.


🔹 Otros Servicios y Herramientas.

- Jupyter Notebooks → Pruebas y desarrollo iterativo de modelos de IA.

- VS Code → Entorno de desarrollo principal.

--------------------------------------------------------------------------------------- 

## Licencia 📜

Este proyecto está bajo la Licencia MIT. Para más detalles, consulta el archivo LICENSE.

------------------------------------------------------------------------------------------

## Autores ✨

Este proyecto fue desarrollado por el equipo de The Bridge, y los siguientes colaboradores contribuyeron al mismo. Haz clic en sus nombres para acceder a sus repositorios de GitHub:

[Iñigo Pascual Aguirre](https://github.com/Inigopascuaguir/BIBAI.git), [Vanessa López Aguilera](https://github.com/VanessaLpzAg/BIBAI.git), [Irene Arrabé Prieto](https://github.com/JZubiaga13/Proyecto_BBDD), [Félix De Molina]() y [Nacho Miguelsanz Praena](). 


¡Gracias por usar BIBAI! 😄

Os deseamos mucho éxito en vuestro aprendizaje. ¡Confía en el proceso y sigue adelante!