# French Anki Generator 🇫🇷🇻🇳

Tự động tạo Anki flashcard từ danh sách từ vựng tiếng Pháp.

**Card type:** Typing card — nhìn nghĩa tiếng Việt, gõ từ tiếng Pháp.

## Tính năng

- 🤖 Tự động sinh nghĩa tiếng Việt, câu ví dụ tiếng Pháp, và bản dịch
- 🔊 Tạo audio phát âm tiếng Pháp (word + example sentence)
- 📦 Xuất file `.apkg` import trực tiếp vào Anki
- 💾 Cache thông minh — chạy lại không generate lại dữ liệu cũ
- ⌨️ Typing card — buộc người học phải gõ từ tiếng Pháp

## Yêu cầu

- Python 3.10+
- [Ollama](https://ollama.com/) đang chạy với model đã pull
- Kết nối internet (cho gTTS audio)

## Cài đặt

```bash
# Clone project
cd french-anki-generator

# Tạo virtual environment (khuyến nghị)
python -m venv .venv
source .venv/bin/activate

# Cài dependencies
pip install -r requirements.txt

# Pull Ollama model
ollama pull qwen3
```

## Sử dụng

### 1. Chuẩn bị vocabulary

Tạo file `input/vocab.txt`:

```text
bonjour
maison
manger
voyage
prendre
avoir besoin de
faire attention à
```

### 2. Chạy tool

```bash
python generate.py
```

### 3. Import vào Anki

File output: `output/french_vietnamese.apkg`

Mở Anki → File → Import → chọn file `.apkg`.

## CLI Options

```bash
python generate.py                           # Mặc định
python generate.py --input input/vocab.txt   # Custom input
python generate.py --output output/a1.apkg   # Custom output
python generate.py --deck "French A1"        # Custom deck name
python generate.py --force                   # Bỏ qua cache, generate lại
python generate.py --verbose                 # Debug logging
```

## Cấu hình

Chỉnh file `config.yaml`:

```yaml
llm:
  provider: ollama
  model: qwen3               # Thay đổi model Ollama
  host: http://localhost:11434

tts:
  engine: gtts
  language: fr

anki:
  deck_name: "French - Vietnamese"
  package_name: "french_vietnamese.apkg"

paths:
  input: "input/vocab.txt"
  output_dir: "output"
  cache: "cache"
```

## Card Preview

### Front (người học thấy)

```
🇻🇳 xin chào

🔊 [French pronunciation]

Type the French word:
[________________________]
```

### Back (sau khi trả lời)

```
🇫🇷 bonjour

🔊 [Word Audio]

🇻🇳 xin chào

━━━━━━━━━━━━━━━━━━

📝 Bonjour, comment allez-vous ?

🇻🇳 Xin chào, bạn khỏe không?

🔊 [Example Audio]
```

## Cấu trúc project

```
french-anki-generator/
├── generate.py          # Entry point
├── config.yaml          # Configuration
├── requirements.txt     # Dependencies
├── input/
│   └── vocab.txt        # Danh sách từ
├── output/
│   └── french_vietnamese.apkg
├── cache/
│   ├── llm/             # Cached LLM responses
│   └── audio/           # Cached audio files
├── src/
│   ├── parser.py        # Đọc vocab file
│   ├── llm.py           # Ollama integration
│   ├── tts.py           # Text-to-speech
│   ├── anki.py          # Anki deck builder
│   ├── models.py        # Data structures
│   └── utils.py         # Utilities
└── tests/
    ├── test_parser.py
    ├── test_llm.py
    └── test_anki.py
```

## Tests

```bash
python -m pytest tests/ -v
```

## Troubleshooting

### "Ollama is not running"

```bash
ollama serve
```

### Audio không tạo được

Kiểm tra kết nối internet (gTTS sử dụng Google Translate API).

### Model not found

```bash
ollama pull qwen3
```
