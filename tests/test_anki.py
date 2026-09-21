"""Tests for the Anki deck builder."""

import os
import tempfile
import zipfile

import pytest

from src.anki import create_anki_deck
from src.models import VocabularyItem


class TestCreateAnkiDeck:
    """Tests for Anki deck creation."""

    def _make_item(
        self,
        word: str,
        meaning: str = "test meaning",
        example_fr: str = "Example sentence.",
        example_vi: str = "Câu ví dụ.",
        word_audio: str = None,
    ) -> VocabularyItem:
        """Create a test VocabularyItem."""
        return VocabularyItem(
            word=word,
            meaning=meaning,
            example_fr=example_fr,
            example_vi=example_vi,
            word_audio_path=word_audio,
        )

    def test_create_basic_deck(self):
        """Should create an .apkg file with valid items."""
        items = [
            self._make_item("bonjour", "xin chào"),
            self._make_item("maison", "ngôi nhà"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "test.apkg")
            result = create_anki_deck(items, "Test Deck", output)

            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
            assert zipfile.is_zipfile(result)

    def test_skip_incomplete_items(self):
        """Items without all required fields should be skipped."""
        items = [
            self._make_item("bonjour", "xin chào"),
            VocabularyItem(word="failed_word", failed=True),
            VocabularyItem(word="no_meaning"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "test.apkg")
            result = create_anki_deck(items, "Test Deck", output)
            assert os.path.exists(result)

    def test_deck_with_audio_files(self):
        """Should include word audio files in the package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio = os.path.join(tmpdir, "bonjour.mp3")
            with open(audio, "wb") as f:
                f.write(b"fake audio data")

            items = [
                self._make_item("bonjour", "xin chào", word_audio=audio),
            ]

            output = os.path.join(tmpdir, "test.apkg")
            result = create_anki_deck(items, "Test Deck", output)

            assert os.path.exists(result)
            with zipfile.ZipFile(result, "r") as zf:
                names = zf.namelist()
                assert "media" in names

    def test_empty_items_list(self):
        """Should still create a valid .apkg with no cards."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "test.apkg")
            result = create_anki_deck([], "Empty Deck", output)
            assert os.path.exists(result)

    def test_output_directory_creation(self):
        """Should create output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = os.path.join(tmpdir, "nested", "dir", "test.apkg")
            items = [self._make_item("bonjour", "xin chào")]
            result = create_anki_deck(items, "Test Deck", output)
            assert os.path.exists(result)
