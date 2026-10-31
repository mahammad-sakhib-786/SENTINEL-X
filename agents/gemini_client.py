
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

if not MODEL:
    raise RuntimeError("GEMINI_MODEL is missing from .env")

client = genai.Client(api_key=api_key)


def generate_structured(model_schema, prompt: str):
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": model_schema,
        },
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return model_schema.model_validate_json(response.text)
