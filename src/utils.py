"""Utility functions for French Anki Generator."""

import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Optional

import yaml


logger = logging.getLogger("french_anki")


# ─── Default Configuration ────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "llm": {
        "provider": "ollama",
        "model": "qwen3",
        "host": "http://localhost:11434",
    },
    "tts": {
        "engine": "gtts",
        "language": "fr",
    },
    "anki": {
        "deck_name": "French - Vietnamese",
        "package_name": "french_vietnamese.apkg",
    },
    "paths": {
        "input": "input/vocab.txt",
        "output_dir": "output",
        "cache": "cache",
    },
}


# ─── Config Loading ──────────────────────────────────────────────────────────

def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file, falling back to defaults.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Merged configuration dictionary.
    """
    config = _deep_copy_dict(DEFAULT_CONFIG)

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        config = _deep_merge(config, user_config)
        logger.debug("Loaded config from %s", config_path)
    else:
        logger.warning("Config file %s not found, using defaults", config_path)

    return config


def _deep_copy_dict(d: dict) -> dict:
    """Create a deep copy of a nested dictionary."""
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _deep_copy_dict(v)
        else:
            result[k] = v
    return result


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base dictionary."""
    result = _deep_copy_dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ─── Directory Setup ─────────────────────────────────────────────────────────

def ensure_directories(config: dict) -> None:
    """Create all required directories if they don't exist.

    Args:
        config: The application configuration dictionary.
    """
    cache_dir = config["paths"]["cache"]
    output_dir = config["paths"]["output_dir"]

    dirs = [
        output_dir,
        os.path.join(cache_dir, "llm"),
        os.path.join(cache_dir, "audio"),
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.debug("Ensured directory: %s", d)


# ─── Filename Sanitization ───────────────────────────────────────────────────

def sanitize_filename(text: str) -> str:
    """Convert text to a safe filename.

    Handles French accents, spaces, and special characters.

    Args:
        text: The text to convert to a filename.

    Returns:
        A sanitized filename string (without extension).

    Examples:
        >>> sanitize_filename("bonjour")
        'bonjour'
        >>> sanitize_filename("avoir besoin de")
        'avoir_besoin_de'
        >>> sanitize_filename("faire attention à")
        'faire_attention_a'
    """
    # Normalize unicode (decompose accents)
    normalized = unicodedata.normalize("NFD", text.lower())
    # Remove combining diacritical marks (accents)
    ascii_text = "".join(
        c for c in normalized if unicodedata.category(c) != "Mn"
    )
    # Replace spaces and special chars with underscores
    safe = re.sub(r"[^a-z0-9]", "_", ascii_text)
    # Collapse multiple underscores
    safe = re.sub(r"_+", "_", safe)
    # Strip leading/trailing underscores
    safe = safe.strip("_")
    return safe or "unnamed"


# ─── JSON Parsing ────────────────────────────────────────────────────────────

def safe_json_parse(text: str) -> Optional[dict]:
    """Parse JSON from text, handling common LLM output issues.

    Strips markdown code fences, extra whitespace, and attempts
    to extract JSON from mixed content.

    Args:
        text: The raw text to parse.

    Returns:
        Parsed dictionary, or None if parsing fails.
    """
    if not text:
        return None

    cleaned = text.strip()

    # Remove markdown code fences
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r"\{[^{}]*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try to find nested JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


# ─── Logging ─────────────────────────────────────────────────────────────────

def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: If True, set log level to DEBUG. Otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )


# ─── Cache Helpers ───────────────────────────────────────────────────────────

def get_llm_cache_path(word: str, cache_dir: str) -> str:
    """Get the cache file path for a word's LLM data.

    Args:
        word: The French word or phrase.
        cache_dir: The base cache directory.

    Returns:
        Path to the cache JSON file.
    """
    filename = sanitize_filename(word) + ".json"
    return os.path.join(cache_dir, "llm", filename)


def get_word_audio_cache_path(word: str, cache_dir: str) -> str:
    """Get the cache file path for a word's audio.

    Args:
        word: The French word or phrase.
        cache_dir: The base cache directory.

    Returns:
        Path to the audio file.
    """
    filename = sanitize_filename(word) + ".mp3"
    return os.path.join(cache_dir, "audio", filename)



def load_llm_cache(word: str, cache_dir: str) -> Optional[dict]:
    """Load cached LLM data for a word.

    Args:
        word: The French word or phrase.
        cache_dir: The base cache directory.

    Returns:
        Cached data dict, or None if not cached.
    """
    path = get_llm_cache_path(word, cache_dir)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.debug("Failed to load cache for '%s': %s", word, e)
    return None


def save_llm_cache(word: str, data: dict, cache_dir: str) -> None:
    """Save LLM data to cache.

    Args:
        word: The French word or phrase.
        data: The data dictionary to cache.
        cache_dir: The base cache directory.
    """
    path = get_llm_cache_path(word, cache_dir)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.warning("Failed to save cache for '%s': %s", word, e)
