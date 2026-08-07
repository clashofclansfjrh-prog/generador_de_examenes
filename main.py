import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import google.generativeai as genai
import json

# Leer la clave desde el entorno del servidor (SEGURO)
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash') 

app = FastAPI()
# ... (el resto del código queda exactamente igual)

# Permitir peticiones desde el frontend HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generar-examen")
async def generar_examen(archivo: UploadFile = File(...)):
    if not archivo.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    try:
        # Extraer texto del PDF
        lector_pdf = PyPDF2.PdfReader(archivo.file)
        texto_extraido = ""
        for pagina in lector_pdf.pages:
            texto_extraido += pagina.extract_text() or ""

        if not texto_extraido.strip():
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF (podría ser una imagen escaneada).")

        # Instrucción para la IA
        instrucciones = f"""
        Eres un profesor experto. Lee el siguiente texto y genera un examen de opción múltiple de 3 preguntas.
        Debes responder ÚNICAMENTE en formato JSON válido con la siguiente estructura exacta, sin texto adicional ni bloques de código markdown:
        [
            {{
                "pregunta": "Texto de la pregunta",
                "opciones": ["Opción A", "Opción B", "Opción C"],
                "respuesta_correcta": "Opción A"
            }}
        ]
        
        Texto del PDF:
        {texto_extraido[:8000]}
        """

        # Generar contenido
        respuesta_ia = model.generate_content(instrucciones)
        texto_limpio = respuesta_ia.text.replace("```json", "").replace("```", "").strip()
        
        return {"estado": "éxito", "examen": json.loads(texto_limpio)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))