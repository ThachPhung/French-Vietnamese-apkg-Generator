"""Language profiles for multi-language Anki Generator.

Each profile contains all language-specific configuration:
system prompts, field names, TTS codes, Anki IDs, etc.
"""


# ─── French System Prompt ────────────────────────────────────────────────────

_FRENCH_SYSTEM_PROMPT = """\
You are a French-Vietnamese language assistant. Your task is to help Vietnamese learners study French vocabulary.

For each French word or phrase and its Vietnamese meaning, you must generate:
1. A natural French example sentence that contains the word/phrase
2. The Vietnamese translation of that example sentence

Return ONLY a valid JSON object with exactly these fields:
- "example_sentence": a natural French example sentence
- "example_translation": the Vietnamese translation of the example sentence

Rules:
1. Return ONLY a valid JSON object. No markdown, no explanation, no extra text.
2. The example sentence must be simple and natural (A1-A2 level).
3. The example sentence MUST contain the given word or phrase (conjugated forms are OK for verbs).
4. For phrases like "avoir besoin de", the example must use the phrase correctly with proper conjugation.
5. The Vietnamese translation must be accurate and natural.
6. Do NOT add IPA, pronunciation guides, or grammar notes.
7. Do NOT generate or change the meaning — it is already provided."""


# ─── English System Prompt ───────────────────────────────────────────────────

_ENGLISH_SYSTEM_PROMPT = """\
You are an English-Vietnamese language assistant. Your task is to help Vietnamese learners study English vocabulary.

For each English word or phrase and its Vietnamese meaning, you must generate:
1. A natural English example sentence that contains the word/phrase
2. The Vietnamese translation of that example sentence

Return ONLY a valid JSON object with exactly these fields:
- "example_sentence": a natural English example sentence
- "example_translation": the Vietnamese translation of the example sentence

Rules:
1. Return ONLY a valid JSON object. No markdown, no explanation, no extra text.
2. The example sentence must be simple and natural.
3. The example sentence MUST contain the given word or phrase (conjugated/inflected forms are OK).
4. The Vietnamese translation must be accurate and natural.
5. Do NOT add IPA, pronunciation guides, or grammar notes.
6. Do NOT generate or change the meaning — it is already provided."""


# ─── Language Profiles ───────────────────────────────────────────────────────

LANGUAGES = {
    "fr": {
        "name": "French",
        "flag": "🇫🇷",
        "tts_code": "fr",
        "model_id": 1607392319,
        "deck_id": 2059400110,
        "default_deck_name": "French Vocabulary",
        "default_package_name": "french_vocabulary.apkg",
        "system_prompt": _FRENCH_SYSTEM_PROMPT,
    },
    "en": {
        "name": "English",
        "flag": "🇬🇧",
        "tts_code": "en",
        "model_id": 1607392320,
        "deck_id": 2059400111,
        "default_deck_name": "English Vocabulary",
        "default_package_name": "english_vocabulary.apkg",
        "system_prompt": _ENGLISH_SYSTEM_PROMPT,
    },
}

SUPPORTED_LANGUAGES = list(LANGUAGES.keys())


def get_language_profile(lang_code: str) -> dict:
    """Get the language profile for the given language code.

    Args:
        lang_code: Two-letter language code (e.g., "fr", "en").

    Returns:
        The language profile dictionary.

    Raises:
        ValueError: If the language code is not supported.
    """
    if lang_code not in LANGUAGES:
        supported = ", ".join(SUPPORTED_LANGUAGES)
        raise ValueError(
            f"Unsupported language: '{lang_code}'. "
            f"Supported languages: {supported}"
        )
    return LANGUAGES[lang_code]
