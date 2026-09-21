"""Text-to-Speech module for French Anki Generator.

Generates French audio pronunciation using gTTS (Google Text-to-Speech).
Designed as a pluggable interface so TTS engines can be swapped.
"""

import logging
import os
from typing import Optional

from gtts import gTTS


logger = logging.getLogger("french_anki")


def generate_audio(
    text: str,
    output_path: str,
    language: str = "fr",
) -> bool:
    """Generate audio for the given text and save to file.

    If the output file already exists, skips generation (cache hit).

    Args:
        text: The French text to synthesize.
        output_path: Path where the MP3 file will be saved.
        language: Language code for TTS (default: "fr").

    Returns:
        True if audio file exists (generated or cached), False on failure.
    """
    # Cache check: skip if file already exists
    if os.path.exists(output_path):
        logger.debug("Audio cache hit: %s", output_path)
        return True

    try:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        tts = gTTS(text=text, lang=language)
        tts.save(output_path)

        logger.debug("Generated audio: %s", output_path)
        return True

    except Exception as e:
        logger.warning("Failed to generate audio for '%s': %s", text, e)
        # Clean up partial file if it exists
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        return False


def generate_word_audio(
    word: str,
    output_path: str,
    language: str = "fr",
) -> Optional[str]:
    """Generate pronunciation audio for a single word.

    Args:
        word: The French word or phrase.
        output_path: Path where the MP3 file will be saved.
        language: Language code for TTS.

    Returns:
        The output path if successful, None otherwise.
    """
    success = generate_audio(word, output_path, language)
    return output_path if success else None


def generate_example_audio(
    example_sentence: str,
    output_path: str,
    language: str = "fr",
) -> Optional[str]:
    """Generate audio for an example sentence.

    Args:
        example_sentence: The French example sentence.
        output_path: Path where the MP3 file will be saved.
        language: Language code for TTS.

    Returns:
        The output path if successful, None otherwise.
    """
    success = generate_audio(example_sentence, output_path, language)
    return output_path if success else None
