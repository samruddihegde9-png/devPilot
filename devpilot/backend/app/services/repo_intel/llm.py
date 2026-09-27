"""
Thin, optional wrapper around the OpenAI chat completions API.

Repository Intelligence works fully offline (deterministic, heuristic-based
overview/architecture/issues/tests and keyword-retrieval Q&A). If
`OPENAI_API_KEY` is set in the environment, callers may use `call_llm` to
turn the *already-extracted, repository-grounded* facts into better prose or
to answer a natural-language question — but every caller must pass
`fail_silently=True`-style handling and have a non-LLM fallback, since this
call can fail (no key, no network, rate limit) and must never block the
feature or invent facts on its own.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_ENDPOINT = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
_TIMEOUT_SECONDS = 120


def llm_available() -> bool:
    return bool(settings.openai_api_key)


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 700) -> str | None:
    """Returns the model's text, or None if the call couldn't be made/failed.

    Never raises — every failure mode (no key, network error, bad response)
    returns None so callers fall back to their deterministic output.
    Auth errors (401/403) and quota errors (429) are logged at WARNING so
    the server log tells the operator what is wrong without leaking key material.
    """
    if not settings.openai_api_key:
        return None

    try:
        response = httpx.post(
            _ENDPOINT,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.2,
            },
            timeout=_TIMEOUT_SECONDS,
        )
        # Log specific HTTP error codes with a helpful hint before raising.
        if response.status_code == 401:
            logger.warning(
                "OpenAI returned 401 Unauthorized — check that OPENAI_API_KEY in "
                "backend/.env is a valid key (starts with 'sk-'). Falling back to "
                "heuristic mode."
            )
            return None
        if response.status_code == 429:
            logger.warning(
                "OpenAI returned 429 Too Many Requests — rate limit or quota exceeded. "
                "Falling back to heuristic mode."
            )
            return None
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return text.strip() if text else None
    except httpx.TimeoutException:
        logger.warning("OpenAI request timed out after %ds. Falling back to heuristic mode.", _TIMEOUT_SECONDS)
        return None
    except httpx.HTTPStatusError as exc:
        logger.warning("OpenAI HTTP error %s: %s. Falling back to heuristic mode.", exc.response.status_code, exc)
        return None
    except httpx.HTTPError as exc:
        logger.warning("OpenAI network error: %s. Falling back to heuristic mode.", exc)
        return None
    except (KeyError, IndexError, ValueError) as exc:
        logger.warning("Unexpected OpenAI response format: %s. Falling back to heuristic mode.", exc)
        return None
