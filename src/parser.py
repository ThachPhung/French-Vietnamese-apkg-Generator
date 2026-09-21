"""Vocabulary file parser for Anki Generator.

Parses vocab files with format: Word | Vietnamese meaning
"""

import logging
from pathlib import Path
from typing import List, Tuple


logger = logging.getLogger("anki_generator")


def parse_vocab(file_path: str) -> List[Tuple[str, str]]:
    """Parse a vocabulary file and return deduplicated (word, meaning) pairs.

    Expected format per line:
        Word | Vietnamese meaning

    Strips whitespace, skips blank lines and comments, removes duplicates.

    Args:
        file_path: Path to the vocabulary text file.

    Returns:
        A list of (word, meaning) tuples.

    Raises:
        FileNotFoundError: If the vocabulary file does not exist.
        ValueError: If no valid entries are found, or a line is missing meaning.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Vocabulary file not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    entries: List[Tuple[str, str]] = []
    seen: set = set()

    with open(path, "r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip comment lines
            if line.startswith("#"):
                continue

            # Parse word | meaning
            if "|" not in line:
                raise ValueError(
                    f"Line {line_number}: Missing '|' separator. "
                    f"Expected format: Word | Vietnamese meaning\n"
                    f"  Got: {line}"
                )

            parts = line.split("|", maxsplit=1)
            word = parts[0].strip()
            meaning = parts[1].strip()

            if not word:
                raise ValueError(
                    f"Line {line_number}: Empty word before '|'"
                )

            if not meaning:
                raise ValueError(
                    f"Line {line_number}: Empty meaning after '|' for word '{word}'"
                )

            # Deduplicate (case-insensitive on word)
            word_lower = word.lower()
            if word_lower in seen:
                logger.debug(
                    "Line %d: Skipping duplicate '%s'", line_number, word
                )
                continue

            seen.add(word_lower)
            entries.append((word, meaning))
            logger.debug("Line %d: Added '%s' | '%s'", line_number, word, meaning)

    if not entries:
        raise ValueError(f"No valid entries found in {file_path}")

    logger.info("Parsed %d unique entry(ies) from %s", len(entries), file_path)
    return entries
