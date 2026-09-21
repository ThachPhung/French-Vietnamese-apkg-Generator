"""Tests for the vocabulary parser."""

import os
import tempfile

import pytest

from src.parser import parse_vocab


class TestParseVocab:
    """Tests for parse_vocab function."""

    def _write_temp_file(self, content: str) -> str:
        """Helper to create a temp file with content."""
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_simple_entries(self):
        """Parse basic word | meaning entries."""
        path = self._write_temp_file("bonjour | xin chào\nmaison | ngôi nhà\n")
        try:
            result = parse_vocab(path)
            assert result == [("bonjour", "xin chào"), ("maison", "ngôi nhà")]
        finally:
            os.unlink(path)

    def test_skip_empty_lines(self):
        """Empty lines should be ignored."""
        path = self._write_temp_file("bonjour | xin chào\n\n\nmaison | ngôi nhà\n")
        try:
            result = parse_vocab(path)
            assert result == [("bonjour", "xin chào"), ("maison", "ngôi nhà")]
        finally:
            os.unlink(path)

    def test_strip_whitespace(self):
        """Whitespace around word and meaning should be stripped."""
        path = self._write_temp_file("  bonjour  |  xin chào  \n  maison  |  ngôi nhà  \n")
        try:
            result = parse_vocab(path)
            assert result == [("bonjour", "xin chào"), ("maison", "ngôi nhà")]
        finally:
            os.unlink(path)

    def test_deduplicate_words(self):
        """Duplicate words should be removed (case-insensitive)."""
        path = self._write_temp_file("bonjour | xin chào\nBonjour | chào\n")
        try:
            result = parse_vocab(path)
            assert len(result) == 1
            assert result[0] == ("bonjour", "xin chào")
        finally:
            os.unlink(path)

    def test_phrases(self):
        """Multi-word phrases should be handled correctly."""
        path = self._write_temp_file("avoir besoin de | cần\nfaire attention à | chú ý\n")
        try:
            result = parse_vocab(path)
            assert result == [("avoir besoin de", "cần"), ("faire attention à", "chú ý")]
        finally:
            os.unlink(path)

    def test_skip_comments(self):
        """Lines starting with # should be skipped."""
        path = self._write_temp_file("# Comment\nbonjour | xin chào\n# Another\nmaison | nhà\n")
        try:
            result = parse_vocab(path)
            assert result == [("bonjour", "xin chào"), ("maison", "nhà")]
        finally:
            os.unlink(path)

    def test_missing_separator_raises_error(self):
        """Lines without | should raise ValueError."""
        path = self._write_temp_file("bonjour\n")
        try:
            with pytest.raises(ValueError, match="Missing '\\|' separator"):
                parse_vocab(path)
        finally:
            os.unlink(path)

    def test_empty_meaning_raises_error(self):
        """Empty meaning after | should raise ValueError."""
        path = self._write_temp_file("bonjour | \n")
        try:
            with pytest.raises(ValueError, match="Empty meaning"):
                parse_vocab(path)
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            parse_vocab("/nonexistent/path/vocab.txt")

    def test_empty_file(self):
        """Should raise ValueError for empty files."""
        path = self._write_temp_file("")
        try:
            with pytest.raises(ValueError, match="No valid entries"):
                parse_vocab(path)
        finally:
            os.unlink(path)

    def test_preserves_order(self):
        """Should preserve the original order of entries."""
        path = self._write_temp_file("voyage | chuyến đi\nbonjour | xin chào\n")
        try:
            result = parse_vocab(path)
            assert result == [("voyage", "chuyến đi"), ("bonjour", "xin chào")]
        finally:
            os.unlink(path)

    def test_meaning_with_pipe_in_value(self):
        """Meaning containing extra | should be kept (split on first | only)."""
        path = self._write_temp_file("prendre | lấy, cầm | to take\n")
        try:
            result = parse_vocab(path)
            assert result[0] == ("prendre", "lấy, cầm | to take")
        finally:
            os.unlink(path)
