"""Tests for the LLM module."""

import json
import os
import tempfile

import pytest

from src.llm import generate_vocabulary_data, _build_user_prompt
from src.utils import safe_json_parse


class TestBuildUserPrompt:
    """Tests for the user prompt builder."""

    def test_includes_word_and_meaning(self):
        prompt = _build_user_prompt("bonjour", "xin chào")
        assert "bonjour" in prompt
        assert "xin chào" in prompt
        assert "example_fr" in prompt

    def test_phrase(self):
        prompt = _build_user_prompt("avoir besoin de", "cần")
        assert "avoir besoin de" in prompt
        assert "cần" in prompt


class TestSafeJsonParse:
    """Tests for JSON parsing utility used by LLM module."""

    def test_valid_json(self):
        text = '{"example_fr": "Bonjour!", "example_vi": "Xin chào!"}'
        result = safe_json_parse(text)
        assert result is not None
        assert result["example_fr"] == "Bonjour!"

    def test_json_with_markdown_fences(self):
        text = '```json\n{"example_fr": "Bonjour!", "example_vi": "Xin chào!"}\n```'
        result = safe_json_parse(text)
        assert result is not None
        assert result["example_fr"] == "Bonjour!"

    def test_json_embedded_in_text(self):
        text = 'Here is the result: {"example_fr": "La maison.", "example_vi": "Ngôi nhà."} end'
        result = safe_json_parse(text)
        assert result is not None
        assert result["example_fr"] == "La maison."

    def test_invalid_json(self):
        result = safe_json_parse("This is not JSON at all")
        assert result is None

    def test_empty_input(self):
        result = safe_json_parse("")
        assert result is None

    def test_none_input(self):
        result = safe_json_parse(None)
        assert result is None


class TestGenerateVocabularyDataCache:
    """Tests for LLM cache behavior (no actual LLM calls)."""

    def test_cache_hit(self):
        """When cache exists, should return cached data without calling LLM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cache file
            llm_cache_dir = os.path.join(tmpdir, "llm")
            os.makedirs(llm_cache_dir)

            cache_data = {
                "example_fr": "Bonjour, comment allez-vous ?",
                "example_vi": "Xin chào, bạn khỏe không?",
            }
            cache_path = os.path.join(llm_cache_dir, "bonjour.json")
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f)

            # Should use cache (no Ollama needed)
            config = {"host": "http://localhost:99999", "model": "test"}
            item = generate_vocabulary_data(
                word="bonjour",
                meaning="xin chào",
                config=config,
                cache_dir=tmpdir,
                use_cache=True,
            )

            assert item.meaning == "xin chào"
            assert item.example_fr == "Bonjour, comment allez-vous ?"
            assert item.example_vi == "Xin chào, bạn khỏe không?"
            assert not item.failed

    def test_cache_miss_no_ollama(self):
        """When cache misses and Ollama is unreachable, should mark as failed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "llm"))

            config = {"host": "http://localhost:99999", "model": "test"}
            item = generate_vocabulary_data(
                word="bonjour",
                meaning="xin chào",
                config=config,
                cache_dir=tmpdir,
                use_cache=True,
            )

            assert item.failed
            assert item.error_message
