# Phụ lục — Chuẩn thi quốc tế & mapping trình độ

**Trạng thái:** 🟢 Đã chốt

> Tham chiếu cấu trúc các kỳ thi mà [Exam template](../06-exam/srs-exam.md) phải mô phỏng được, và bảng quy đổi trình độ dùng cho trường `level` của nội dung. Số liệu cấu trúc thi lấy theo công bố chính thức của đơn vị tổ chức tại thời điểm 7/2026 — **content_editor xác minh lại trước khi dựng template thật** (kỳ thi có thể đổi format, VD HSK 3.0).

## 1. Khung trình độ & mapping

| CEFR | IELTS | TOEIC LR | Cambridge | VSTEP | HSK (2.0) | JLPT | TOPIK |
|---|---|---|---|---|---|---|---|
| C2 | 8.5–9.0 | — | CPE | — | — | — | — |
| C1 | 7.0–8.0 | 945+ | CAE | Bậc 5 | HSK 6 | N1 | 6 |
| B2 | 5.5–6.5 | 785–940 | FCE | Bậc 4 | HSK 5 | N2 | 5 |
| B1 | 4.0–5.0 | 550–780 | PET | Bậc 3 | HSK 4 | N3 | 3–4 |
| A2 | 3.0–3.5 | 225–545 | KET | Bậc 2 | HSK 3 | N4 | 2 |
| A1 | 2.0–2.5 | 120–220 | YLE Flyers | Bậc 1 | HSK 1–2 | N5 | 1 |

> Mapping mang tính tham chiếu (các bảng quy đổi công khai không hoàn toàn thống nhất). Hệ thống lưu `level` theo thang gốc của từng khung + cột `cefr_equiv` để lọc/so sánh chéo ngôn ngữ.

## 2. Cấu trúc kỳ thi (mức template)

### IELTS (Academic/General)
| Phần | Thời gian | Câu | Chấm |
|---|---|---|---|
| Listening | 30' (+10' chuyển đáp án bản giấy — bản máy không có) | 40 | Tự động; raw → band |
| Reading | 60' | 40 | Tự động; raw → band |
| Writing (Task 1 + 2) | 60' | 2 | AI + GV theo 4 tiêu chí: TA/TR, CC, LR, GRA (band 0–9, bước 0.5) |
| Speaking (Part 1–3) | 11–14' | 3 phần | Ghi âm thi thử; AI + GV: FC, LR, GRA, P |
Band tổng = trung bình 4 kỹ năng làm tròn 0.25→0.5.

### TOEIC
- **LR**: Listening 45'/100 câu (Part 1–4) + Reading 75'/100 câu (Part 5–7); thang 10–990 (mỗi phần 5–495), quy đổi từ raw theo bảng ETS.
- **SW** (thi riêng): Speaking ~20'/11 câu; Writing ~60'/8 câu; mỗi phần 0–200.

### VSTEP (bậc 3–5)
| Phần | Thời gian | Nội dung |
|---|---|---|
| Nghe | ~40' | 35 câu, 3 phần |
| Đọc | 60' | 40 câu, 4 bài đọc |
| Viết | 60' | 2 task (thư/email + luận) |
| Nói | 12' | 3 phần (tương tác xã hội, thảo luận giải pháp, phát triển chủ đề) |
Thang 0–10; quy bậc: 4.0–5.5 = B1, 6.0–8.0 = B2, 8.5–10 = C1.

### Cambridge KET (A2 Key) / PET (B1 Preliminary) / FCE (B2 First)
- KET: Reading&Writing 60' · Listening 30' · Speaking 8–10' (thi cặp).
- PET: Reading 45' · Writing 45' · Listening 30' · Speaking 12–17'.
- FCE: Reading&UoE 75' · Writing 80' · Listening 40' · Speaking 14'.
- Thang Cambridge Scale 80–230; YLE (Starters/Movers/Flyers) chấm bằng khiên 1–5, template dạng "đạt khiên".

### HSK (khung 2.0 — 6 cấp) + HSKK
| Cấp | Phần & thời gian | Điểm đạt |
|---|---|---|
| HSK 1–2 | Nghe + Đọc (~35–55') | 120/200 |
| HSK 3 | Nghe + Đọc + Viết (~90') | 180/300 |
| HSK 4–6 | Nghe + Đọc + Viết (~105–140') | 180/300 |
| HSKK sơ/trung/cao | Nói qua ghi âm 17–25' | 60/100 |
> HSK 3.0 (9 cấp) đang triển khai dần — template thiết kế **data-driven** để thêm khung mới không sửa code.

### JLPT (N5 → N1)
| Cấp | Phần | Thời gian | Thang |
|---|---|---|---|
| N1–N2 | Kiến thức ngôn ngữ (từ vựng/ngữ pháp) + Đọc · Nghe | 110'+55' / 105'+50' | 0–60 × 3 phần = 180; điểm đạt N1: 100, N2: 90; điểm liệt 19/phần |
| N3–N5 | Từ vựng · Ngữ pháp+Đọc · Nghe | tùy cấp | 180 điểm; đạt N3: 95, N4: 90, N5: 80 |
Không có phần Nói/Viết — practice nói/viết tiếng Nhật vẫn dùng được ngoài exam.

### TOPIK
| Kỳ | Phần | Thời gian | Thang |
|---|---|---|---|
| TOPIK I (cấp 1–2) | Nghe 30 câu + Đọc 40 câu | 100' | 200; cấp 1 ≥80, cấp 2 ≥140 |
| TOPIK II (cấp 3–6) | Nghe 50 + Viết 4 (51–54) + Đọc 50 | 180' | 300; cấp 3 ≥120 … cấp 6 ≥230 |
Viết TOPIK II: 2 câu điền (51–52) + đoạn 200–300 ký tự (53) + luận 600–700 ký tự (54) — chấm AI + GV.

## 3. Yêu cầu suy ra cho hệ thống

1. **Template data-driven**: mọi kỳ thi mô tả bằng dữ liệu (phần, thời gian, số câu, thang, bảng quy đổi, điểm liệt per phần) — thêm/sửa kỳ thi không sửa code.
2. **Quy đổi điểm**: hỗ trợ 3 kiểu — bảng tra (TOEIC raw→scaled), công thức trung bình (IELTS band), ngưỡng đạt/liệt per phần (JLPT, HSK, TOPIK).
3. **Điểm liệt per phần** (JLPT) và **điểm đạt theo cấp** (TOPIK II nhiều cấp trong 1 bài) phải biểu diễn được.
4. **Thi cặp Speaking** (Cambridge) v1 không mô phỏng — ghi rõ giới hạn với trung tâm.
5. Font/hiển thị: Hán tự (zh/ja), Hangul, furigana/pinyin — đã ghi ở [NFR-I18N-02](../01-kien-truc/06-yeu-cau-phi-chuc-nang.md).

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo bản nháp đầu tiên | Claude |
| 2026-07-16 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
