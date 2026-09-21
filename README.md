# Anki Vocabulary Generator

Generate [Anki](https://apps.ankiweb.net/) flashcard decks (`.apkg`) from plain-text vocabulary lists. Uses a local LLM via [Ollama](https://ollama.com/) to create example sentences and [gTTS](https://github.com/pndurette/gTTS) for pronunciation audio.

Currently supports **French → Vietnamese** and **English → Vietnamese**.

## Features

- **Multi-language** — Generate cards for French (`--lang fr`) or English (`--lang en`)
- **LLM-powered examples** — Automatically generates a natural example sentence + Vietnamese translation for each word using Ollama (runs 100% locally, no API keys needed)
- **Audio pronunciation** — Word-level TTS audio embedded directly in each card
- **Typing cards** — Cards show the Vietnamese meaning; you type the target-language word. Anki checks your answer character by character
- **Smart caching** — Re-running the same vocabulary won't regenerate existing data. Cache is stored per-language so French and English never conflict
- **Daily incremental workflow** — Each word gets a deterministic GUID. Import multiple `.apkg` files into the same Anki deck on different days and Anki will merge them without creating duplicates
- **Configurable** — Override the deck name, output path, LLM model, and more via CLI flags or `config.yaml`

## Prerequisites

| Dependency | Purpose | Install |
|---|---|---|
| **Python 3.10+** | Runtime | [python.org](https://www.python.org/) or via `conda` |
| **Ollama** | Local LLM for example sentences | [ollama.com](https://ollama.com/) |
| **Internet** | gTTS audio generation (calls Google Translate TTS) | — |

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/anki-vocabulary-generator.git
cd anki-vocabulary-generator

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Or use conda:
# conda create -n anki python=3.11 && conda activate anki

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull an Ollama model
ollama pull qwen3
```

## Quick Start

### 1. Start Ollama

```bash
ollama serve
```

> This single `ollama serve` instance handles **both** French and English — the tool sends different system prompts depending on the language.

### 2. Create a vocabulary file

Create a plain text file with one entry per line in the format `Word | Vietnamese meaning`:

```text
# French example (input/french_day01.txt)
bonjour | xin chào
maison | ngôi nhà
avoir besoin de | cần
```

```text
# English example (input/english_day01.txt)
accomplish | hoàn thành
ambiguous | mơ hồ, không rõ ràng
nevertheless | tuy nhiên
```

- Lines starting with `#` are treated as comments and ignored
- Blank lines are ignored
- Whitespace around `|` is stripped automatically
- Duplicate words (case-insensitive) are deduplicated

### 3. Run the generator

```bash
# French (default)
python generate.py input/french_day01.txt

# English
python generate.py input/english_day01.txt --lang en
```

### 4. Import into Anki

1. Open Anki → **File → Import**
2. Select the generated `.apkg` file from `output/`
3. Done! Your cards appear in the deck

On subsequent days, create a new vocabulary file, run the generator, and import again. Anki merges new words into the existing deck without duplicating old ones.

## CLI Reference

```
usage: generate.py [-h] [--lang {fr,en}] [--output OUTPUT] [--deck DECK]
                   [--config CONFIG] [--force] [--verbose]
                   input
```

| Flag | Short | Description | Default |
|---|---|---|---|
| `input` | — | Path to vocabulary file (required) | — |
| `--lang` | `-l` | Target language: `fr` or `en` | `fr` (or from `config.yaml`) |
| `--output` | `-o` | Output `.apkg` file path | `output/<lang>_vocabulary.apkg` |
| `--deck` | `-d` | Anki deck name | `French Vocabulary` / `English Vocabulary` |
| `--config` | `-c` | Path to config file | `config.yaml` |
| `--force` | `-f` | Ignore cache, regenerate everything | `false` |
| `--verbose` | `-v` | Enable debug logging | `false` |

### Examples

```bash
# Basic French generation
python generate.py input/day01.txt

# English with custom deck name
python generate.py input/english.txt --lang en --deck "IELTS Vocabulary"

# Custom output path
python generate.py input/day01.txt -o output/day01_french.apkg

# Force regenerate (ignore cache)
python generate.py input/day01.txt --force

# Debug mode
python generate.py input/day01.txt --verbose
```

## Configuration

All settings can be customized in `config.yaml`:

```yaml
language: fr              # Default language: "fr" or "en"

llm:
  provider: ollama
  model: qwen3            # Any Ollama model (qwen3, llama3, mistral, etc.)
  host: http://localhost:11434

tts:
  engine: gtts

anki:
  deck_name: ""           # Leave empty → uses language profile default
  package_name: ""        # Leave empty → uses language profile default

paths:
  output_dir: "output"
  cache: "cache"
```

**Priority order** for settings: CLI flags > `config.yaml` > language profile defaults.

## Project Structure

```
.
├── generate.py            # CLI entry point
├── config.yaml            # User configuration
├── requirements.txt       # Python dependencies
├── src/
│   ├── __init__.py
│   ├── languages.py       # Language profiles (prompts, IDs, TTS codes)
│   ├── llm.py             # Ollama API integration
│   ├── models.py          # VocabularyItem dataclass
│   ├── parser.py          # Vocabulary file parser
│   ├── tts.py             # gTTS audio generation
│   └── utils.py           # Config loading, caching, helpers
├── tests/
│   ├── test_anki.py
│   ├── test_llm.py
│   └── test_parser.py
├── input/                 # Your vocabulary files (gitignored)
├── output/                # Generated .apkg files (gitignored)
└── cache/                 # LLM + audio cache (gitignored)
    ├── llm/
    │   ├── fr/            # French LLM cache
    │   └── en/            # English LLM cache
    └── audio/
        ├── fr/            # French audio cache
        └── en/            # English audio cache
```

## Card Layout

### Front (Question)

```
🇻🇳 xin chào

🔊 [pronunciation audio]

[________________________]   ← Type your answer here
```

### Back (Answer)

```
[Character-by-character comparison: green = correct, red = wrong]

🇫🇷 bonjour                  (or 🇬🇧 hello for English)

🔊 [pronunciation audio]

🇻🇳 xin chào

────────────────────

📝 Bonjour, comment allez-vous ?

🇻🇳 Xin chào, bạn khỏe không?
```

## Adding a New Language

To add support for another language (e.g., Japanese, Spanish):

1. **Add a language profile** in [`src/languages.py`](src/languages.py):
   - Write a system prompt for the LLM
   - Choose a unique `model_id` and `deck_id` (any integer, must not collide with existing ones)
   - Set the `tts_code` (see [gTTS supported languages](https://gtts.readthedocs.io/en/latest/module.html#languages-gtts-lang))

2. That's it. The new language code will automatically appear in `--lang` choices.

```python
# Example: adding Spanish
LANGUAGES["es"] = {
    "name": "Spanish",
    "flag": "🇪🇸",
    "tts_code": "es",
    "model_id": 1607392321,
    "deck_id": 2059400112,
    "default_deck_name": "Spanish Vocabulary",
    "default_package_name": "spanish_vocabulary.apkg",
    "system_prompt": _SPANISH_SYSTEM_PROMPT,
}
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Troubleshooting

| Problem | Solution |
|---|---|
| `ERROR: Ollama is not running` | Run `ollama serve` in a separate terminal |
| `No module named 'genanki'` | Run `pip install -r requirements.txt` |
| Audio files not generated | Check your internet connection (gTTS requires it) |
| Duplicate cards after re-import | This shouldn't happen — each word has a stable GUID. Use `--force` if you want to regenerate content |
| LLM generates bad examples | Try a different model (`model: llama3` in `config.yaml`) or re-run with `--force` |

## License

MIT
