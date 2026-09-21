"""Ollama LLM integration for French Anki Generator.

Handles communication with Ollama API to generate French example sentences
and their Vietnamese translations. Meaning is provided from the input file.
"""

import json
import logging
import time
from typing import Optional

import requests

from src.models import VocabularyItem
from src.utils import (
    load_llm_cache,
    safe_json_parse,
    save_llm_cache,
)


logger = logging.getLogger("french_anki")

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


# ─── System Prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a French-Vietnamese language assistant. Your task is to help Vietnamese learners study French vocabulary.

For each French word or phrase and its Vietnamese meaning, you must generate:
1. A natural French example sentence that contains the word/phrase
2. The Vietnamese translation of that example sentence

Return ONLY a valid JSON object with exactly these fields:
- "example_fr": a natural French example sentence
- "example_vi": the Vietnamese translation of the example sentence

Rules:
1. Return ONLY a valid JSON object. No markdown, no explanation, no extra text.
2. The example sentence must be simple and natural (A1-A2 level).
3. The example sentence MUST contain the given word or phrase (conjugated forms are OK for verbs).
4. For phrases like "avoir besoin de", the example must use the phrase correctly with proper conjugation.
5. The Vietnamese translation must be accurate and natural.
6. Do NOT add IPA, pronunciation guides, or grammar notes.
7. Do NOT generate or change the meaning — it is already provided."""


def _build_user_prompt(word: str, meaning: str) -> str:
    """Build the user prompt for a vocabulary word.

    Args:
        word: The French word or phrase.
        meaning: The Vietnamese meaning.

    Returns:
        The user prompt string.
    """
    return (
        f"French: {word}\n"
        f"Vietnamese meaning: {meaning}\n\n"
        f'Return JSON: {{"example_fr": "...", "example_vi": "..."}}'
    )


# ─── Ollama Connection ───────────────────────────────────────────────────────

def check_ollama_connection(host: str) -> bool:
    """Check if Ollama is running and accessible.

    Args:
        host: The Ollama host URL (e.g., http://localhost:11434).

    Returns:
        True if Ollama is accessible, False otherwise.
    """
    try:
        response = requests.get(host, timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        return False
    except Exception:
        return False


# ─── LLM Generation ─────────────────────────────────────────────────────────

def _call_ollama(word: str, meaning: str, config: dict) -> Optional[dict]:
    """Call Ollama API to generate example sentence and translation.

    Args:
        word: The French word or phrase.
        meaning: The Vietnamese meaning.
        config: The LLM configuration dictionary.

    Returns:
        Parsed JSON dict with example_fr and example_vi,
        or None on failure.
    """
    host = config.get("host", "http://localhost:11434")
    model = config.get("model", "qwen3")
    url = f"{host}/api/chat"

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(word, meaning)},
        ],
        "format": {
            "type": "object",
            "properties": {
                "example_fr": {"type": "string"},
                "example_vi": {"type": "string"},
            },
            "required": ["example_fr", "example_vi"],
        },
    }

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()

    result = response.json()
    content = result.get("message", {}).get("content", "")

    parsed = safe_json_parse(content)
    if parsed is None:
        logger.debug("Failed to parse LLM response for '%s': %s", word, content[:200])
        return None

    # Validate required fields
    required = ["example_fr", "example_vi"]
    if not all(parsed.get(k) for k in required):
        logger.debug("Missing required fields for '%s': %s", word, parsed)
        return None

    return parsed


def generate_vocabulary_data(
    word: str,
    meaning: str,
    config: dict,
    cache_dir: str,
    use_cache: bool = True,
) -> VocabularyItem:
    """Generate example sentence and translation for a French word.

    Meaning is provided from the input file (not generated).
    Checks cache first. If not cached, calls Ollama with retry logic.
    On persistent failure, returns item marked as failed.

    Args:
        word: The French word or phrase.
        meaning: The Vietnamese meaning (from input).
        config: The LLM configuration dictionary.
        cache_dir: The base cache directory.
        use_cache: Whether to use caching.

    Returns:
        A VocabularyItem populated with LLM data.
    """
    item = VocabularyItem(word=word, meaning=meaning)

    # Check cache
    if use_cache:
        cached = load_llm_cache(word, cache_dir)
        if cached:
            item.example_fr = cached.get("example_fr", "")
            item.example_vi = cached.get("example_vi", "")
            logger.debug("Cache hit for '%s'", word)
            return item

    # Call LLM with retries
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            data = _call_ollama(word, meaning, config)
            if data:
                item.example_fr = data["example_fr"]
                item.example_vi = data["example_vi"]

                # Save to cache
                if use_cache:
                    save_llm_cache(word, data, cache_dir)

                return item

            last_error = "Invalid JSON response"
            logger.debug(
                "Attempt %d/%d for '%s': %s",
                attempt, MAX_RETRIES, word, last_error,
            )

        except requests.ConnectionError as e:
            last_error = f"Connection error: {e}"
            logger.debug(
                "Attempt %d/%d for '%s': %s",
                attempt, MAX_RETRIES, word, last_error,
            )
        except requests.Timeout as e:
            last_error = f"Timeout: {e}"
            logger.debug(
                "Attempt %d/%d for '%s': %s",
                attempt, MAX_RETRIES, word, last_error,
            )
        except requests.HTTPError as e:
            last_error = f"HTTP error: {e}"
            logger.debug(
                "Attempt %d/%d for '%s': %s",
                attempt, MAX_RETRIES, word, last_error,
            )
        except Exception as e:
            last_error = f"Unexpected error: {e}"
            logger.debug(
                "Attempt %d/%d for '%s': %s",
                attempt, MAX_RETRIES, word, last_error,
            )

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    # All retries exhausted
    item.failed = True
    item.error_message = last_error
    logger.warning("Failed to generate data for '%s': %s", word, last_error)
    return item
