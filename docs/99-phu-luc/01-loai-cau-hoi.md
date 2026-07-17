# Phụ lục — Catalog loại câu hỏi

**Trạng thái:** 🟢 Đã chốt

> Danh mục chuẩn các Question Type. Ngân hàng câu hỏi ([SRS Nội dung](../10-noi-dung/srs-noi-dung.md)) lưu `question.type` theo mã dưới đây; nội dung câu hỏi là JSONB validate theo JSON Schema per loại (định nghĩa khi implement). Cột "Chấm" cho biết tầng chấm ([SRS Chấm bài](../08-cham-bai/srs-cham-bai.md)).

## 1. Loại câu hỏi dùng chung (mọi kỹ năng)

| Mã | Tên | Mô tả tương tác | Chấm | v1 |
|---|---|---|---|---|
| `mcq_single` | Trắc nghiệm 1 đáp án | Chọn 1 trong 3–5 lựa chọn (text/ảnh/audio) | Tự động | ✅ |
| `mcq_multi` | Trắc nghiệm nhiều đáp án | Chọn nhiều; chấm toàn phần hoặc từng phần (cài đặt) | Tự động | ✅ |
| `true_false` | Đúng / Sai (/ Not Given) | 2 hoặc 3 lựa chọn (True/False/NG cho IELTS Reading) | Tự động | ✅ |
| `fill_blank` | Điền vào chỗ trống | 1+ chỗ trống trong câu/đoạn; nhiều đáp án chấp nhận được, tùy chọn bỏ qua hoa/thường | Tự động | ✅ |
| `matching` | Nối cặp | Kéo/chọn nối 2 cột (từ–nghĩa, câu hỏi–đoạn, người–ý kiến) | Tự động | ✅ |
| `ordering` | Sắp xếp thứ tự | Kéo sắp xếp từ→câu, câu→đoạn, đoạn→bài | Tự động | ✅ |
| `dropdown_blank` | Chọn từ trong ô trống | Chỗ trống là dropdown lựa chọn (cloze chọn) | Tự động | ✅ |
| `short_answer` | Trả lời ngắn | Gõ 1–vài từ (IELTS "NO MORE THAN TWO WORDS") | Tự động (khớp mẫu) | ✅ |
| `table_completion` | Hoàn thành bảng | Điền ô trống trong bảng/biểu đồ/ghi chú | Tự động | ✅ |

## 2. Kỹ năng Nghe (Listening)

Mọi loại ở mục 1 + audio đính kèm (câu lẻ hoặc question group dùng chung audio). Riêng:

| Mã | Tên | Mô tả | Chấm | v1 |
|---|---|---|---|---|
| `dictation` | Chép chính tả | Nghe đoạn ngắn, gõ lại nguyên văn; chấm theo tỉ lệ từ đúng (word-level diff) | Tự động | ✅ |
| `listen_map` | Ghi nhãn bản đồ/sơ đồ | Nghe và gán nhãn vị trí trên ảnh (IELTS map labelling) — v1 dùng dropdown per vị trí | Tự động | ✅ |

Cài đặt audio per câu hỏi/nhóm: số lần nghe tối đa, có cho tua không, tốc độ phát.

## 3. Kỹ năng Nói (Speaking)

| Mã | Tên | Mô tả | Chấm | v1 |
|---|---|---|---|---|
| `read_aloud` | Đọc thành tiếng | Đọc đoạn văn hiển thị; chấm phát âm scripted (accuracy/fluency/completeness) | AI (+GV) | ✅ |
| `repeat_sentence` | Nghe & nhắc lại | Nghe câu → nhắc lại (không thấy text); chấm khớp + phát âm | AI (+GV) | ✅ |
| `describe_image` | Mô tả tranh/biểu đồ | Nói tự do theo tranh trong N giây (chuẩn bị + nói) | AI unscripted (+GV) | ✅ |
| `open_response` | Trả lời câu hỏi mở | Câu hỏi text/audio → trả lời tự do (IELTS Part 1/3, HSKK, TOPIK nói) | AI unscripted (+GV) | ✅ |
| `monologue` | Độc thoại theo chủ đề | Cue card + thời gian chuẩn bị 1' + nói 1–2' (IELTS Part 2) | AI unscripted (+GV) | ✅ |
| `shadowing` | Nói theo (shadowing) | Nghe từng câu và nói theo; v1 chấm như read_aloud từng câu | AI (+GV) | Should |

## 4. Kỹ năng Đọc (Reading)

Mọi loại ở mục 1 gắn với passage (question group) + riêng:

| Mã | Tên | Mô tả | Chấm | v1 |
|---|---|---|---|---|
| `heading_matching` | Nối tiêu đề đoạn | Chọn heading cho từng đoạn (IELTS) | Tự động | ✅ |
| `cloze_reading` | Đọc điền từ (cloze) | Đoạn văn đục lỗ nhiều chỗ (TOEIC Part 6, JLPT 文法) | Tự động | ✅ |

Hiển thị: passage hỗ trợ hệ chữ CJK + ruby text (furigana/pinyin — bật per câu hỏi theo level).

## 5. Kỹ năng Viết (Writing)

| Mã | Tên | Mô tả | Chấm | v1 |
|---|---|---|---|---|
| `sentence_transform` | Viết lại câu | Viết lại câu theo gợi ý/từ cho trước; nhiều đáp án đúng | Tự động (mẫu) + GV xem lại | ✅ |
| `sentence_build` | Dựng câu từ từ cho sẵn | Sắp xếp/chia từ tạo câu đúng (phổ biến JLPT 語順) | Tự động | ✅ |
| `short_writing` | Viết đoạn ngắn | 50–100 từ/ký tự theo đề (email, tin nhắn — TOEIC W, TOPIK 51-52) | AI + GV | ✅ |
| `essay` | Viết luận | Bài luận theo đề + rubric chuẩn thi (IELTS Task 1/2, TOPIK 54) | AI + GV | ✅ |
| `handwriting_upload` | Viết tay chụp ảnh | Nộp ảnh bài viết tay (chữ Hán, luyện viết kanji) | GV 100% | ✅ |

## 6. Flashcard (trong khóa học)

Không phải question type trong ngân hàng câu hỏi — flashcard là content block của [Khóa học](../04-khoa-hoc/srs-khoa-hoc.md) (thẻ 2 mặt + spaced repetition). Ghi ở đây để tránh nhầm.

## 7. Ánh xạ loại câu hỏi ↔ kỳ thi (ví dụ tiêu biểu)

| Kỳ thi | Loại dùng nhiều |
|---|---|
| IELTS | `mcq_single`, `true_false` (T/F/NG), `matching`, `heading_matching`, `fill_blank`, `short_answer`, `table_completion`, `listen_map`, `essay`, `monologue`, `open_response` |
| TOEIC LR | `mcq_single` (Part 1–4 với ảnh/audio), `cloze_reading` (Part 5–6), question group đọc (Part 7) |
| HSK/HSKK | `true_false`, `matching`, `mcq_single`, `ordering` (sắp xếp câu), `fill_blank` (điền Hán tự), `read_aloud`, `open_response`, `describe_image` |
| JLPT | `mcq_single` (từ vựng/ngữ pháp/đọc/nghe), `sentence_build` (語順), `cloze_reading` |
| TOPIK | `mcq_single`, `fill_blank` (I), `short_writing` + `essay` (II 51–54), nghe `mcq_single` |
| VSTEP | 4 kỹ năng tương tự IELTS + `essay`, `open_response` |

## 8. Quy ước JSONB (mức thiết kế)

Mỗi loại có JSON Schema riêng; khung chung:

```json
{
  "prompt": { "text": "...", "media": ["file_id"], "ruby": false },
  "options": [ ... ],            // per loại
  "answer_key": { ... },          // per loại; null với loại AI/GV chấm
  "scoring": { "points": 1, "partial": false, "case_sensitive": false },
  "speaking": { "prep_seconds": 60, "speak_seconds": 120, "max_retries": 2 },  // loại nói
  "audio": { "max_plays": 2, "allow_seek": false }                              // loại nghe
}
```

## Câu hỏi mở cần chốt

| # | Câu hỏi | Quyết định | Ngày chốt |
|---|---|---|---|
| 1 | 24 loại v1 như trên đủ chưa — có cần `listen_map` dạng kéo-thả thật (thay vì dropdown) ngay v1? | **Chốt:** 24 loại đủ cho v1; listen_map dùng dropdown, kéo-thả để v2 | 2026-07-16 |
| 2 | `handwriting_upload` (viết tay chữ Hán) đưa vào Must cho thị trường tiếng Trung/Nhật? | **Chốt:** Có — nâng thành Must/✅ v1 cho thị trường tiếng Trung/Nhật | 2026-07-16 |

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo bản nháp đầu tiên | Claude |
| 2026-07-16 | Chốt toàn bộ câu hỏi mở (quyết định ghi trong bảng), chuyển trạng thái Đã chốt | Chủ sản phẩm |
