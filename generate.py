#!/usr/bin/env python3
"""French Anki Generator - Main entry point.

Generates Anki .apkg flashcard decks from French vocabulary lists.
Uses Ollama (local LLM) for examples and gTTS for audio.

Supports daily incremental workflow:
  Day 1: python generate.py vocab_day01.txt
  Day 2: python generate.py vocab_day02.txt
  Import all .apkg files into Anki → same deck, no duplicates.

Usage:
    python generate.py vocab.txt
    python generate.py vocab.txt -o output/french_a1.apkg
    python generate.py vocab.txt --deck "French A1"
    python generate.py vocab.txt --force
"""

import argparse
import os
import sys

from src.anki import create_anki_deck
from src.llm import check_ollama_connection, generate_vocabulary_data
from src.models import VocabularyItem
from src.parser import parse_vocab
from src.tts import generate_word_audio
from src.utils import (
    ensure_directories,
    get_word_audio_cache_path,
    load_config,
    setup_logging,
)


# ─── ANSI Colors ─────────────────────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header():
    """Print the application header."""
    print()
    print(f"{BOLD}French Anki Generator{RESET}")
    print("=" * 40)
    print()


def print_summary(
    total: int,
    successful: int,
    failed: int,
    audio_count: int,
    output_path: str,
):
    """Print the final summary."""
    print()
    print("─" * 40)
    print()

    if successful > 0:
        print(f"  {GREEN}✓{RESET} {successful} cards created")
    if audio_count > 0:
        print(f"  {GREEN}✓{RESET} {audio_count} audio files ready")
    if failed > 0:
        print(f"  {RED}✗{RESET} {failed} failed")

    print()
    print(f"  {BOLD}Output:{RESET}")
    print(f"  {output_path}")
    print()


def main():
    """Main entry point for the French Anki Generator."""

    # ── Parse arguments ──────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="Generate Anki flashcards from French vocabulary lists.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python generate.py vocab.txt
  python generate.py vocab_day01.txt -o output/day01.apkg
  python generate.py vocab.txt --deck "French A1"
  python generate.py vocab.txt --force
        """,
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to vocabulary file (format: French word | Vietnamese meaning)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output .apkg file path (default: from config.yaml)",
    )
    parser.add_argument(
        "--deck", "-d",
        type=str,
        default=None,
        help="Anki deck name (default: from config.yaml)",
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force regenerate all data (ignore cache)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # ── Setup ────────────────────────────────────────────────────────────
    setup_logging(verbose=args.verbose)
    print_header()

    # Load config
    config = load_config(args.config)

    # Apply CLI overrides
    input_path = args.input
    deck_name = args.deck or config["anki"]["deck_name"]
    package_name = args.output or os.path.join(
        config["paths"]["output_dir"],
        config["anki"]["package_name"],
    )
    cache_dir = config["paths"]["cache"]
    use_cache = not args.force

    # Ensure directories exist
    ensure_directories(config)

    # ── Check Ollama ─────────────────────────────────────────────────────
    llm_host = config["llm"]["host"]
    print(f"  Checking Ollama at {llm_host}...", end=" ")
    sys.stdout.flush()

    if not check_ollama_connection(llm_host):
        print(f"{RED}FAILED{RESET}")
        print()
        print(f"  {RED}ERROR: Ollama is not running.{RESET}")
        print()
        print(f"  Please start Ollama and try again:")
        print(f"    ollama serve")
        print()
        sys.exit(1)

    print(f"{GREEN}OK{RESET}")

    # ── Parse vocabulary ─────────────────────────────────────────────────
    print(f"  Input: {input_path}")

    try:
        entries = parse_vocab(input_path)
    except FileNotFoundError as e:
        print(f"\n  {RED}ERROR: {e}{RESET}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n  {RED}ERROR: {e}{RESET}")
        sys.exit(1)

    total = len(entries)
    print(f"  Words found: {total}")
    print()

    # ── Process vocabulary ───────────────────────────────────────────────
    items: list[VocabularyItem] = []
    successful = 0
    failed = 0
    audio_count = 0

    tts_language = config["tts"]["language"]

    for idx, (word, meaning) in enumerate(entries, start=1):
        prefix = f"  [{idx}/{total}]"
        print(f"{prefix} {word:<30s}", end=" ", flush=True)

        # ── LLM: Generate example sentence + translation ─────────
        item = generate_vocabulary_data(
            word=word,
            meaning=meaning,
            config=config["llm"],
            cache_dir=cache_dir,
            use_cache=use_cache,
        )

        if item.failed:
            print(f"{RED}✗ {item.error_message}{RESET}")
            failed += 1
            items.append(item)
            continue

        # ── TTS: Generate word audio ─────────────────────────────
        word_audio_path = get_word_audio_cache_path(word, cache_dir)
        result = generate_word_audio(word, word_audio_path, tts_language)
        if result:
            item.word_audio_path = result
            audio_count += 1

        items.append(item)
        successful += 1
        print(f"{GREEN}✓{RESET}")

    # ── Create Anki deck ─────────────────────────────────────────────────
    print()
    print(f"  Generating Anki deck...", end=" ", flush=True)

    complete_items = [item for item in items if item.is_complete]

    if not complete_items:
        print(f"{RED}FAILED{RESET}")
        print(f"\n  {RED}ERROR: No complete vocabulary items to create deck.{RESET}")
        sys.exit(1)

    output_path = create_anki_deck(
        items=complete_items,
        deck_name=deck_name,
        output_path=package_name,
    )

    print(f"{GREEN}OK{RESET}")

    # ── Summary ──────────────────────────────────────────────────────────
    print_summary(
        total=total,
        successful=successful,
        failed=failed,
        audio_count=audio_count,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()
