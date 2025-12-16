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
        You are an educational architect. Analyze the following content and extract:
        1. A concise summary (max 200 words).
        2. Divide the content into logical knowledge chunks (max 500 words each).

        Return JSON format:
        {{
            "summary": "...",
            "chunks": ["chunk 1 text...", "chunk 2 text..."]
        }}

        Content:
        {text[:20000]} 
        """
        # Truncate to avoid context limit in prototype

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful educational assistant. Output valid JSON."},
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
        Create {quantity} assessment items (Multiple Choice or True/False) based strictly on this text.
        
        Return JSON format:
        {{
            "items": [
                {{
                    "type": "multiple_choice",
                    "stem": "Question text...",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": "Why..."
                }},
                {{
                    "type": "true_false",
                    "stem": "Statement...",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "explanation": "Why..."
                }}
            ]
        }}

        Text:
        {chunk_text[:5000]}
        """

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert assessment creator. Output valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content_str = response.choices[0].message.content
        data = json.loads(content_str)
        return ItemResult(items=data["items"])
