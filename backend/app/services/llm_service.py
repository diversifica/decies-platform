import json
import logging

import openai
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class StructureResult(BaseModel):
    summary: str
    chunks: list[str]  # Just text content for now


class ItemResult(BaseModel):
    items: list[dict]


class LLMService:
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            logger.warning("OPENAI_API_KEY not set. LLMService will fail if called.")

    def generate_structure_e2(self, text: str) -> StructureResult:
        """
        Step E2: Transforms raw text into a summary and logical chunks.
        """
        if not self.client:
            raise ValueError("LLM Client not configured (missing OPENAI_API_KEY)")

        prompt = f"""
        Eres un arquitecto educativo. Analiza el siguiente contenido y extrae:
        1. Un resumen conciso (máximo 200 palabras) EN ESPAÑOL.
        2. Divide el contenido en fragmentos lógicos de conocimiento
           (máximo 500 palabras cada uno) EN ESPAÑOL.

        Devuelve formato JSON:
        {{
            "summary": "...",
            "chunks": ["fragmento 1...", "fragmento 2..."]
        }}

        Contenido:
        {text[:20000]} 
        """
        # Truncate to avoid context limit in prototype

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente educativo útil. "
                        "Genera respuestas en ESPAÑOL. Output valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content_str = response.choices[0].message.content
        data = json.loads(content_str)
        return StructureResult(summary=data["summary"], chunks=data["chunks"])

    def generate_items_e4(self, chunk_text: str, quantity: int = 3) -> ItemResult:
        """
        Step E4: Generates assessment items from a text chunk.
        """
        if not self.client:
            raise ValueError("LLM Client not configured")

        prompt = f"""
        Crea {quantity} preguntas de evaluación (Opción Múltiple o Verdadero/Falso) 
        basadas estrictamente en este texto. TODAS LAS PREGUNTAS DEBEN ESTAR EN ESPAÑOL.
        
        Devuelve formato JSON:
        {{
            "items": [
                {{
                    "type": "multiple_choice",
                    "stem": "Texto de la pregunta en español...",
                    "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
                    "correct_answer": "Opción A",
                    "explanation": "Explicación en español..."
                }},
                {{
                    "type": "true_false",
                    "stem": "Afirmación en español...",
                    "options": ["Verdadero", "Falso"],
                    "correct_answer": "Verdadero",
                    "explanation": "Explicación en español..."
                }}
            ]
        }}

        Texto:
        {chunk_text[:5000]}
        """

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un experto creador de evaluaciones. "
                        "Genera TODO el contenido en ESPAÑOL. Output valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content_str = response.choices[0].message.content
        data = json.loads(content_str)
        return ItemResult(items=data["items"])
