# app/services/generate.py
from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI  # pip install openai


# Usa variable de entorno para el modelo
OPENAI_MODEL = os.getenv("OPENAI_TIPS_MODEL", "gpt-4.1-mini")


def _get_client() -> Optional[OpenAI]:
    """
    Devuelve un cliente de OpenAI si hay API key,
    o None si no está configurada (para hacer fallback).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def generate_tip_body(
    title: str,
    raw_text: str,
    topic_slug: str,
    max_chars: int = 280,
) -> str:
    """
    Dado un título, un resumen/artículo y el topic, genera
    un tip corto, claro y accionable.

    Si no hay API key configurada, devuelve el raw_text recortado.
    """
    client = _get_client()
    if client is None:
        # Fallback: sin IA, solo saneamos y recortamos
        text = (raw_text or title or "").strip().replace("\n", " ")
        return text[:max_chars]

    prompt = f"""
You are an assistant that writes short, practical daily tips for a mobile app.

Topic: {topic_slug}
Article title: {title}

Article excerpt (may be noisy or partial):
\"\"\"{raw_text[:1500]}\"\"\"  # limitamos por si el feed viene larguísimo

Write ONE short actionable tip in Spanish, in 1-2 sentences, no more than {max_chars} characters.
- It must sound natural and friendly.
- Focus on what the user can DO or remember today.
- Do NOT mention that this comes from an article or RSS or AI.
- Do NOT use emojis.
"""
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system",
                    "content": "You write concise, actionable daily tips in Spanish."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        # Por si acaso se pasa, recortamos
        return text[:max_chars]
    except Exception as e:
        # En caso de error, hacemos fallback silencioso
        print(f"[AI] Error generating tip: {e}")
        text = (raw_text or title or "").strip().replace("\n", " ")
        return text[:max_chars]
