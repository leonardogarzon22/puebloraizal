import json
import traceback
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

load_dotenv()

# ==========================================
# CONFIGURACIÓN DE APIS Y SERVIDOR
# ==========================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="Backend Híbrido CONPES 38 - Comunidad Raizal")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Backend de RaizalGPT activo"}

# Cargar el archivo JSON
ARCHIVO_JSON = "contexto_conpes_38.json"
if os.path.exists(ARCHIVO_JSON):
    with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
        base_datos_conpes = json.load(f)
else:
    base_datos_conpes = []
    print(f"⚠️ Advertencia: No se encontró '{ARCHIVO_JSON}'. El buscador híbrido usará solo IA.")

# Modelos de datos para la API
class ConsultaUsuario(BaseModel):
    pregunta: str

# ==========================================
# LÓGICA DE BÚSQUEDA HÍBRIDA (Mecanismo RAG)
# ==========================================
def buscar_contexto_relevante(pregunta: str, top_n: int = 4):
    if not base_datos_conpes:
        return ""
    
    palabras_clave = pregunta.lower().split()
    fichas_puntuadas = []
    
    for ficha in base_datos_conpes:
        puntuacion = 0
        texto_busqueda = f"{ficha.get('nombre_indicador', '')} {ficha.get('descripcion', '')} {ficha.get('entidad_responsable', '')}".lower()
        
        for palabra in palabras_clave:
            if len(palabra) > 3 and palabra in texto_busqueda:
                puntuacion += 1
                
        if puntuacion > 0:
            ficha_texto = (
                f"- ID Ficha: {ficha.get('id_ficha')}\n"
                f"  Indicador/Producto: {ficha.get('nombre_indicador')}\n"
                f"  Entidad Responsable: {ficha.get('entidad_responsable')}\n"
                f"  Descripción: {ficha.get('descripcion')}\n"
                f"  Relación con Resultados: {ficha.get('relacion_resultado')}\n"
            )
            fichas_puntuadas.append((puntuacion, ficha_texto))
            
    fichas_puntuadas.sort(key=lambda x: x[0], reverse=True)
    contexto_seleccionado = [item[1] for item in fichas_puntuadas[:top_n]]
    
    contexto_plano = []
    for elemento in contexto_seleccionado:
        if isinstance(elemento, list):
            contexto_plano.append(" ".join(map(str, elemento)))
        else:
            contexto_plano.append(str(elemento))

    return "\n".join(contexto_plano)

# ==========================================
# ENDPOINT PRINCIPAL DEL CHATBOT
# ==========================================
@app.post("/api/chat")
async def chat_hibrido(payload: ConsultaUsuario):
    pregunta = payload.pregunta
    contexto_datos = buscar_contexto_relevante(pregunta)
    
    prompt_sistema = (
        "Eres un asistente experto en la Política Pública para la Comunidad Raizal in Bogotá (CONPES 38).\n"
        "Tu misión es responder de manera clara, premium, profesional y empática a las dudas del ciudadano.\n\n"
        "REGLAS DE OPERACIÓN HÍBRIDA:\n"
        "1. A continuación tienes fragmentos de DATOS REALES extraídos de las fichas técnicas del documento oficial:\n"
        f"==== INICIO DATOS CONPES 38 ====\n{contexto_datos if contexto_datos else 'No se encontraron datos exactos en el JSON para esta consulta.'}\n==== FIN DATOS CONPES 38 ====\n\n"
        "2. Usa primordialmente los datos del bloque anterior para responder de forma precisa.\n"
        "3. FUNCIÓN DE VALIDACIÓN CON IA: Si los datos del bloque son escasos o el usuario hace una pregunta conceptual, usa tu conocimiento general sobre el CONPES 38 y políticas públicas en Colombia para complementar la respuesta, garantizando que tenga sentido y coherencia jurídica/institucional.\n"
        "4. Si la información del JSON contradice o no responde en absoluto la pregunta, indícalo amablemente pero ofrece una respuesta estructurada basada en tus capacidades de IA.\n"
        "5. No menciones explícitamente términos como 'el JSON proporcionado' o 'el bloque de datos'. Absorbe la información de manera transparente para el usuario."
    )
    
    try:
        # Configuración adaptada a la nueva generación: 'gemini-3.5-flash'
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        response = model.generate_content(
            f"{prompt_sistema}\n\nPregunta del usuario: {pregunta}"
        )
        return {"respuesta": response.text}
    
    except Exception as e:
       print("\n" + "="*80)
       print("ERROR COMPLETO")
       print(traceback.format_exc())
       print("="*80 + "\n")

       raise HTTPException(
           status_code=500,
           detail=str(e)
       )
        
   

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)