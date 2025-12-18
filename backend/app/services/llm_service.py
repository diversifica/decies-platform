import json
import logging
import uuid

import openai
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class StructureResult(BaseModel):
    summary: str
    chunks: list[str]  # Just text content for now


class ItemResult(BaseModel):
    items: list[dict]


class MicroconceptMatch(BaseModel):
    microconcept_id: uuid.UUID | None = None
    microconcept_code: str | None = None
    microconcept_name: str | None = None


class ChunkMapping(BaseModel):
    chunk_index: int
    microconcept_match: MicroconceptMatch
    confidence: float
    reason: str


class MappingQuality(BaseModel):
    mapping_coverage: float
    mapping_precision_hint: str
    notes: list[str]


class E3MapResult(BaseModel):
    chunk_mappings: list[ChunkMapping]
    quality: MappingQuality


class ItemMicroconceptRef(BaseModel):
    microconcept_id: uuid.UUID | None = None
    microconcept_code: str | None = None
    microconcept_name: str | None = None


class CanonicalItem(BaseModel):
    item_type: str
    stem: str
    options: list[str] | None = None
    correct_answer: str
    explanation: str | None = None
    difficulty: float = 1.0
    microconcept_ref: ItemMicroconceptRef
    source_chunk_index: int


class ValidatedItem(BaseModel):
    index: int
    status: str
    reason: str
    item: CanonicalItem


class E5Quality(BaseModel):
    kept: int
    fixed: int
    dropped: int
    notes: list[str]


class E5ValidationResult(BaseModel):
    validated_items: list[ValidatedItem]
    quality: E5Quality


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

    def map_chunks_to_microconcepts_e3(
        self,
        microconcept_catalog: list[dict],
        chunks_from_e2: list[dict],
    ) -> E3MapResult:
        if not self.client:
            raise ValueError("LLM Client not configured")

        payload = {
            "microconcept_catalog": microconcept_catalog,
            "chunks_from_E2": chunks_from_e2,
        }

        prompt = f"""
        Estás mapeando chunks de contenido a microconceptos existentes.

        Reglas:
        1) Para cada chunk, elige un microconcepto existente si encaja claramente.
        2) Si la confianza es baja, no asignes microconcepto (microconcept_id: null).
        3) Prioriza precisión sobre cobertura.

        Entrada JSON:
        {json.dumps(payload, ensure_ascii=False)}

        Devuelve SOLO JSON válido con este formato:
        {{
          "chunk_mappings": [
            {{
              "chunk_index": 0,
              "microconcept_match": {{
                "microconcept_id": "uuid-or-null",
                "microconcept_code": "string-or-null",
                "microconcept_name": "string-or-null"
              }},
              "confidence": 0.0,
              "reason": "string"
            }}
          ],
          "quality": {{
            "mapping_coverage": 0.0,
            "mapping_precision_hint": "low|medium|high",
            "notes": ["string"]
          }}
        }}
        """

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente educativo útil. "
                        "Devuelve únicamente JSON válido conforme al esquema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content_str = response.choices[0].message.content
        data = json.loads(content_str)
        return E3MapResult.model_validate(data)

    def validate_items_e5(
        self,
        items: list[dict],
        chunks_from_e2: list[dict],
    ) -> E5ValidationResult:
        if not self.client:
            raise ValueError("LLM Client not configured")

        payload = {"items": items, "chunks_from_E2": chunks_from_e2}

        prompt = f"""
        Valida cada ítem respecto al chunk indicado:
        1) ¿La respuesta correcta se deriva del chunk?
        2) ¿Hay ambigüedad?
        3) ¿Opciones consistentes?
        4) ¿Lenguaje apropiado?
        5) ¿Se han colado conceptos no presentes?

        Acciones:
        - ok: ítem válido
        - fix: devuelve versión corregida
        - drop: descartar con razón

        Entrada JSON:
        {json.dumps(payload, ensure_ascii=False)}

        Devuelve SOLO JSON válido con este formato:
        {{
          "validated_items": [
            {{
              "index": 0,
              "status": "ok|fix|drop",
              "reason": "string",
              "item": {{
                "item_type": "mcq|true_false",
                "stem": "string",
                "options": ["string","string"],
                "correct_answer": "string",
                "explanation": "string",
                "difficulty": 1.0,
                "microconcept_ref": {{
                  "microconcept_id": "uuid-or-null",
                  "microconcept_code": "string-or-null",
                  "microconcept_name": "string-or-null"
                }},
                "source_chunk_index": 0
              }}
            }}
          ],
          "quality": {{
            "kept": 0,
            "fixed": 0,
            "dropped": 0,
            "notes": ["string"]
          }}
        }}
        """

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un validador de ítems educativos. "
                        "Devuelve únicamente JSON válido conforme al esquema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content_str = response.choices[0].message.content
        data = json.loads(content_str)
        return E5ValidationResult.model_validate(data)
