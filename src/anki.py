"""Anki deck builder for multi-language Anki Generator.

Creates Anki decks with typing cards using genanki.
Cards show Vietnamese meaning on front, user types the target-language word.

Supports incremental daily workflow:
- Deterministic GUID per word → no duplicates on re-import
- Fixed deck name → all days merge into one deck in Anki
"""

import logging
import os
from typing import List

import genanki

from src.models import VocabularyItem
from src.utils import sanitize_filename


logger = logging.getLogger("anki_generator")


# ─── Custom Note with Stable GUID ───────────────────────────────────────────

class VocabularyNote(genanki.Note):
    """Note with deterministic GUID based on the word.

    This ensures that importing the same word from different .apkg files
    will not create duplicate cards in Anki. Anki uses the GUID to
    identify whether a note already exists.
    """

    @property
    def guid(self):
        # Use the Word field (first field) to generate a stable GUID.
        # Same word → same GUID → Anki treats as same note.
        return genanki.guid_for(self.fields[0])


# ─── CSS ─────────────────────────────────────────────────────────────────────

CARD_CSS = """\
.card {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 20px;
    text-align: center;
    color: #333;
    background-color: #fafafa;
    padding: 20px;
    line-height: 1.6;
}

.meaning {
    font-size: 28px;
    font-weight: bold;
    color: #2c3e50;
    margin: 15px 0;
}

.word {
    font-size: 28px;
    font-weight: bold;
    color: #1a5276;
    margin: 15px 0;
}

.audio {
    margin: 15px 0;
}

.type-answer {
    margin: 15px 0;
}

.prompt {
    font-size: 16px;
    color: #666;
    margin: 10px 0 5px 0;
}

.divider {
    border: none;
    border-top: 2px solid #ddd;
    margin: 20px auto;
    width: 80%;
}

.example {
    font-size: 18px;
    color: #34495e;
    margin: 10px 0;
    font-style: italic;
}

.translation {
    font-size: 16px;
    color: #7f8c8d;
    margin: 10px 0;
}

/* Style the typing input */
input[type="text"] {
    font-size: 22px;
    padding: 8px 12px;
    border: 2px solid #3498db;
    border-radius: 5px;
    text-align: center;
    width: 80%;
    max-width: 400px;
}

/* Correct answer highlight */
code#typeans {
    font-size: 22px;
    padding: 5px;
}
"""


# ─── Card Templates ─────────────────────────────────────────────────────────

def _build_front_template() -> str:
    """Build the front card template."""
    return """\
<div class="meaning">🇻🇳 {{Meaning}}</div>

<div class="audio">{{WordAudio}}</div>

<div class="type-answer">
{{type:Word}}
</div>
"""


def _build_back_template(flag: str) -> str:
    """Build the back card template with the appropriate language flag.

    Args:
        flag: The emoji flag for the target language (e.g., "🇫🇷", "🇬🇧").
    """
    return f"""\
{{{{FrontSide}}}}

<hr class="divider">

<div class="word">{flag} {{{{Word}}}}</div>

<div class="audio">{{{{WordAudio}}}}</div>

<div class="meaning">🇻🇳 {{{{Meaning}}}}</div>

<div class="example">📝 {{{{ExampleSentence}}}}</div>

<div class="translation">🇻🇳 {{{{ExampleTranslation}}}}</div>
"""


# ─── Model Definition ───────────────────────────────────────────────────────

def _create_model(lang_profile: dict) -> genanki.Model:
    """Create the Anki note model with typing card template.

    Args:
        lang_profile: The language profile dictionary.

    Returns:
        A genanki.Model configured for vocabulary typing cards.
    """
    model_id = lang_profile["model_id"]
    lang_name = lang_profile["name"]
    flag = lang_profile["flag"]

    return genanki.Model(
        model_id,
        f"{lang_name} Vocabulary Model",
        fields=[
            {"name": "Word"},
            {"name": "Meaning"},
            {"name": "WordAudio"},
            {"name": "ExampleSentence"},
            {"name": "ExampleTranslation"},
        ],
        templates=[
            {
                "name": f"{lang_name} Typing Card",
                "qfmt": _build_front_template(),
                "afmt": _build_back_template(flag),
            },
        ],
        css=CARD_CSS,
    )


# ─── Deck Creation ──────────────────────────────────────────────────────────

def create_anki_deck(
    items: List[VocabularyItem],
    deck_name: str,
    output_path: str,
    lang_profile: dict,
) -> str:
    """Create an Anki deck from vocabulary items and export as .apkg.

    Uses deterministic GUIDs so the same word always maps to the same
    note. This prevents duplicates when importing multiple .apkg files
    into the same Anki deck.

    Args:
        items: List of VocabularyItem objects with generated data.
        deck_name: Name of the Anki deck.
        output_path: Path for the output .apkg file.
        lang_profile: The language profile dictionary.

    Returns:
        The output file path.
    """
    model = _create_model(lang_profile)
    deck_id = lang_profile["deck_id"]
    deck = genanki.Deck(deck_id, deck_name)
    media_files: List[str] = []

    cards_created = 0
    for item in items:
        if not item.is_complete:
            logger.debug("Skipping incomplete item: '%s'", item.word)
            continue

        # Build audio reference
        word_audio_ref = ""
        if item.word_audio_path and os.path.exists(item.word_audio_path):
            word_audio_filename = os.path.basename(item.word_audio_path)
            word_audio_ref = f"[sound:{word_audio_filename}]"
            media_files.append(item.word_audio_path)

        # Create note with stable GUID
        note = VocabularyNote(
            model=model,
            fields=[
                item.word,
                item.meaning,
                word_audio_ref,
                item.example_sentence,
                item.example_translation,
            ],
        )
        deck.add_note(note)
        cards_created += 1

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Create package with media
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(output_path)

    logger.info("Created Anki deck: %d cards", cards_created)
    return output_path
