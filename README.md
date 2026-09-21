# French Anki Generator 🇫🇷🇻🇳

Tự động tạo Anki flashcard từ danh sách từ vựng tiếng Pháp.

**Card type:** Typing card — nhìn nghĩa tiếng Việt, gõ từ tiếng Pháp.

## Tính năng

- 🤖 Tự động sinh câu ví dụ tiếng Pháp và bản dịch tiếng Việt bằng Ollama (LLM)
- 🔊 Tạo audio phát âm từ vựng tiếng Pháp
- 📦 Xuất file `.apkg` import trực tiếp vào Anki
- 💾 Cache thông minh — chạy lại không generate lại dữ liệu cũ
- ⌨️ Typing card — buộc người học phải gõ từ tiếng Pháp để Anki kiểm tra
- 🔄 **Daily Incremental Workflow** — Hỗ trợ thêm từ mới mỗi ngày vào cùng 1 deck (`French Vocabulary`). Cơ chế Stable GUID đảm bảo các từ trùng lặp ở các ngày khác nhau sẽ không tạo ra card rác trong Anki.

## Yêu cầu

- Python 3.10+
- [Ollama](https://ollama.com/) đang chạy local
- Kết nối internet (dùng gTTS để tạo audio)

## Cài đặt

```bash
# Clone project (nếu chưa có)
cd french-anki-generator

# Tạo virtual environment hoặc conda env (khuyến nghị)
conda create -n anki python=3.11
conda activate anki

# Cài dependencies
pip install -r requirements.txt

# Pull Ollama model (ví dụ qwen3)
ollama pull qwen3
```

## Sử dụng (Workflow Hằng Ngày)

### 1. Chuẩn bị vocabulary

Tạo file text chứa từ vựng cho ngày hôm nay (ví dụ: `vocab_day01.txt`).
**Format bắt buộc:** `Từ/Cụm từ tiếng Pháp | Nghĩa tiếng Việt`

```text
bonjour | xin chào
maison | ngôi nhà
manger | ăn
voyage | chuyến đi
prendre | lấy, cầm
avoir besoin de | cần
faire attention à | chú ý đến
```

*(Tool tự động bỏ qua dòng trống, khoảng trắng thừa và dòng bắt đầu bằng `#`)*

### 2. Chạy tool

Truyền trực tiếp tên file vào lệnh chạy:

```bash
python generate.py vocab_day01.txt
```

### 3. Import vào Anki

File output mặc định sẽ được tạo tại: `output/french_vocabulary.apkg`

Mở Anki → File → Import → chọn file `.apkg`.
Các từ mới sẽ được tự động thêm vào deck **"French Vocabulary"**.

*(Sang ngày 2, bạn chỉ việc tạo `vocab_day02.txt` và chạy lại, sau đó import vào Anki, mọi tiến trình học của ngày cũ vẫn được giữ nguyên)*

## CLI Options

```bash
python generate.py vocab.txt                           # Mặc định xuất ra french_vocabulary.apkg
python generate.py vocab.txt -o output/day02.apkg      # Custom file output
python generate.py vocab.txt --deck "French A1"        # Custom tên deck trong Anki
python generate.py vocab.txt --force                   # Bỏ qua cache, ép tạo lại audio và ví dụ
python generate.py vocab.txt --verbose                 # Bật log chi tiết để debug
```

## Cấu hình

Bạn có thể chỉnh sửa file `config.yaml` mặc định:

```yaml
llm:
  provider: ollama
  model: qwen3               # Đổi model LLM tại đây
  host: http://localhost:11434

tts:
  engine: gtts
  language: fr

anki:
  deck_name: "French Vocabulary"
  package_name: "french_vocabulary.apkg"

paths:
  output_dir: "output"
  cache: "cache"
```

## Card Preview

### Front (Người học thấy)

```
🇻🇳 xin chào

🔊 [Audio phát âm tiếng Pháp]

[________________________]  <-- Ô nhập text (Type the French word)
```

### Back (Sau khi trả lời)

```
[So sánh kết quả gõ: Chữ Xanh (Đúng) / Chữ Đỏ (Sai)]

🇫🇷 bonjour

🔊 [Audio phát âm tiếng Pháp]

🇻🇳 xin chào

━━━━━━━━━━━━━━━━━━

📝 Bonjour, comment allez-vous ?

🇻🇳 Xin chào, bạn khỏe không?
```
