import os
import logging
from openai import OpenAI
from openai import APIConnectionError, APIError, RateLimitError, APITimeoutError

logger = logging.getLogger(__name__)

def obtener_cliente_ia():
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("IA_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=base_url)

def analizar_asistencia(contexto: dict) -> str | None:
    """
    Analiza los datos de asistencia usando Gemini.
    Retorna el texto del análisis o None si hay error.
    """
    cliente = obtener_cliente_ia()
    if not cliente:
        logger.warning("Falta GEMINI_API_KEY. No se puede analizar.")
        return None

    modelo = os.getenv("IA_MODELO", "gemini-3.5-flash")

    # Armar un prompt descriptivo basado en el contexto
    prompt = armar_prompt(contexto)
    
    try:
        resp = cliente.chat.completions.create(
            model=modelo,
            messages=[
                {"role": "system", "content": "Eres un asistente experto en analítica académica. Evalúas reportes de asistencia para detectar patrones, alertar sobre estudiantes en riesgo por inasistencias injustificadas (SE) o incapacidades (INC), y recomendar acciones concretas al instructor. Debes ser directo, usar cifras, evitar generalidades, y redactar máximo 250 palabras en español."},
                {"role": "user", "content": prompt}
            ],
            timeout=30,
            temperature=0.3
        )
        texto = resp.choices[0].message.content
        return texto.strip()
    except (APIConnectionError, APIError, RateLimitError, APITimeoutError) as e:
        logger.error(f"Error de red o API al contactar Gemini: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado en análisis IA: {e}")
        return None

def armar_prompt(contexto: dict) -> str:
    """Construye el texto del prompt basado en los datos del reporte."""
    tipo = contexto.get('tipo', 'general')
    
    texto = f"Contexto del reporte:\n"
    texto += f"- Ficha: {contexto.get('ficha', 'Varias')}\n"
    texto += f"- Programa: {contexto.get('programa', 'Varios')}\n"
    texto += f"- Período: {contexto.get('desde', 'Inicio')} al {contexto.get('hasta', 'Actual')}\n"
    texto += f"- Total Días: {contexto.get('total_dias', 0)}\n"
    texto += f"- Total Estudiantes: {contexto.get('total_estudiantes', 0)}\n\n"
    
    texto += "Resultados por Estudiante:\n"
    for ap in contexto.get('aprendices', []):
        texto += f"[{ap['identificacion']}] {ap['nombre']}: {ap['pct_asistencia']}% (Asiste:{ap['A']}, CE:{ap['CE']}, SE:{ap['SE']}, INC:{ap['INC']})\n"
    
    texto += "\nInstrucciones Específicas:\n"
    if tipo == 'ficha':
        texto += "Analiza a este grupo. Identifica el promedio general estimado. Destaca a los aprendices con el peor % de asistencia y aquellos con más inasistencias Sin Excusa (SE). Identifica si alguien tiene incapacidades reiteradas. ¿Qué recomendaciones das al instructor de esta ficha?"
    elif tipo == 'aprendiz':
        texto += "Analiza el comportamiento individual de este estudiante frente a su ficha. ¿Sus inasistencias son justificadas o sin excusa? ¿Está en riesgo de deserción o bajo rendimiento por fallas? Recomienda una acción a tomar con este caso particular."
    else:
        texto += "Haz un balance general de estos registros. Detecta qué aprendices están en situación crítica (muchas fallas injustificadas o bajo %) y aconseja cómo intervenir de forma grupal o individual."
        
    return texto
