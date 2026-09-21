"""Anki deck builder for French Anki Generator.

Creates Anki decks with typing cards using genanki.
Cards show Vietnamese meaning on front, user types French word.

Supports incremental daily workflow:
- Deterministic GUID per word → no duplicates on re-import
- Fixed deck name → all days merge into one deck in Anki
"""

import hashlib
import logging
import os
from typing import List

import genanki

from src.models import VocabularyItem
from src.utils import sanitize_filename


logger = logging.getLogger("french_anki")


# ─── Stable IDs ──────────────────────────────────────────────────────────────
# Using fixed IDs ensures Anki recognizes updates to existing cards
# rather than creating duplicates on re-import.

MODEL_ID = 1607392319
DECK_ID = 2059400110


# ─── Custom Note with Stable GUID ───────────────────────────────────────────

class FrenchNote(genanki.Note):
    """Note with deterministic GUID based on the French word.

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

FRONT_TEMPLATE = """\
<div class="meaning">🇻🇳 {{Meaning}}</div>

<div class="audio">{{WordAudio}}</div>

<div class="type-answer">
{{type:Word}}
</div>
"""

BACK_TEMPLATE = """\
{{FrontSide}}

<hr class="divider">

<div class="word">🇫🇷 {{Word}}</div>

<div class="audio">{{WordAudio}}</div>

<div class="meaning">🇻🇳 {{Meaning}}</div>

<div class="example">📝 {{ExampleFR}}</div>

<div class="translation">🇻🇳 {{ExampleVI}}</div>
"""


# ─── Model Definition ───────────────────────────────────────────────────────

def _create_model() -> genanki.Model:
    """Create the Anki note model with typing card template.

    Returns:
        A genanki.Model configured for French vocabulary typing cards.
    """
    return genanki.Model(
        MODEL_ID,
        "French Vocabulary Model",
        fields=[
            {"name": "Word"},
            {"name": "Meaning"},
            {"name": "WordAudio"},
            {"name": "ExampleFR"},
            {"name": "ExampleVI"},
        ],
        templates=[
            {
                "name": "French Typing Card",
                "qfmt": FRONT_TEMPLATE,
                "afmt": BACK_TEMPLATE,
            },
        ],
        css=CARD_CSS,
    )


# ─── Deck Creation ──────────────────────────────────────────────────────────

def create_anki_deck(
    items: List[VocabularyItem],
    deck_name: str,
    output_path: str,
) -> str:
    """Create an Anki deck from vocabulary items and export as .apkg.

    Uses deterministic GUIDs so the same word always maps to the same
    note. This prevents duplicates when importing multiple .apkg files
    into the same Anki deck.

    Args:
        items: List of VocabularyItem objects with generated data.
        deck_name: Name of the Anki deck.
        output_path: Path for the output .apkg file.

    Returns:
        The output file path.
    """
    model = _create_model()
    deck = genanki.Deck(DECK_ID, deck_name)
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
        note = FrenchNote(
            model=model,
            fields=[
                item.word,
                item.meaning,
                word_audio_ref,
                item.example_fr,
                item.example_vi,
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
