import json
import os

from dotenv import load_dotenv
from groq import (
    Groq,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
)
from pydantic import ValidationError

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def generate_structured(model_schema, prompt: str):
    """Use Groq first, then Gemini for recoverable failures."""

    if groq_client is not None:
        try:
            schema_json = json.dumps(model_schema.model_json_schema())

            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Return only a valid JSON object matching this "
                            "schema. Do not invent facts.\n"
                            f"Required JSON schema: {schema_json}"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=2000,
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError("Groq returned an empty response.")

            result = model_schema.model_validate_json(content)

            print(f"[AI PROVIDER] Groq | Model: {GROQ_MODEL} | Schema: {model_schema.__name__}")

            return result

        except (APIConnectionError, APITimeoutError) as exc:
            print(
                f"Groq connection issue ({type(exc).__name__}); "
                "trying Gemini fallback."
            )

        except APIStatusError as exc:
            if exc.status_code not in (408, 409, 429) and exc.status_code < 500:
                raise

            print(
                f"Groq API returned HTTP {exc.status_code}; "
                "trying Gemini fallback."
            )

        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            print(
                f"Groq response was invalid ({type(exc).__name__}); "
                "trying Gemini fallback."
            )

    else:
        print("Groq API key is missing; trying Gemini fallback.")

    # Import only when fallback is needed.
    from agents.gemini_client import (
        generate_structured as generate_gemini_structured,
    )

    result = generate_gemini_structured(model_schema, prompt)

    print(f"[AI PROVIDER] Gemini fallback | Schema: {model_schema.__name__}")

    return result