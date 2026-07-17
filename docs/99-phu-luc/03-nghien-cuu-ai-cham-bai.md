# Phụ lục — Nghiên cứu công nghệ AI chấm bài

**Trạng thái:** 🟢 Đã chốt
**Nguồn:** web research 16/07/2026. Giá là giá niêm yết công khai tại thời điểm tra cứu — xác nhận lại với vendor trước khi ký. Đây là căn cứ kỹ thuật cho [SRS Chấm bài](../08-cham-bai/srs-cham-bai.md).

## 1. Speech Assessment (chấm phát âm/fluency)

| Vendor | Anh | Trung | Nhật | Hàn | Chỉ số chính | Giá tham chiếu |
|---|---|---|---|---|---|---|
| **Azure Pronunciation Assessment** | ✓ | ✓ | ✓ | ✓ | Accuracy, Fluency, Completeness, Prosody (prosody chỉ en-US), PronScore | Tính theo STT: ~$0.66/giờ (REST ≤60s) – $1.32/giờ (realtime); free 5h/tháng ([pricing](https://azure.microsoft.com/en-us/pricing/details/speech/)) |
| **SpeechSuper** | ✓ | ✓ | ✓ | ✓ | Phoneme, fluency theo loại câu | $0.004–0.008/request; prepay giảm 15–30% ([pricing](https://www.speechsuper.com/pricing.html)) |
| SpeechAce | ✓ | ✗ | ✗ | ✗ | Phoneme, fluency, grammar, vocab, map IELTS/PTE/CEFR | $40–125/tháng gói + $0.008–0.0125/req 15s |
| Language Confidence | ✓ | ✗ | ✗ | ✗ | Pron, fluency, grammar, vocab, relevance | $0.004–0.01/15s |
| ELSA API | ✓ | ✗ | ✗ | ✗ | Pron, fluency, intonation, grammar, vocab, ước lượng IELTS | $0.008–0.025/15s |
| Google Cloud | — | — | — | — | Không có API pronunciation chuyên dụng | Loại |

**Kết luận:** chỉ **Azure PA** và **SpeechSuper** phủ đủ 4 ngôn ngữ mục tiêu. Đề xuất: Azure PA mặc định (rẻ, 1 vendor phủ PA+STT+TTS), SpeechSuper fallback CJK; vendor chuyên tiếng Anh (ELSA/SpeechAce) là tùy chọn nâng cao chất lượng feedback tiếng Anh sau này.

## 2. STT đa ngôn ngữ

| Phương án | Độ chính xác | Giá | Self-host |
|---|---|---|---|
| **OpenAI Whisper / gpt-4o-transcribe** | Anh ~2.7–8% WER; Trung ~12.8% CER; Nhật 16–18% CER; Hàn cao hơn Anh | $0.006/phút (mini: $0.003/phút) | ✓ (MIT license — large-v3) |
| Azure STT | 100+ ngôn ngữ | $0.66–1.32/giờ | Container enterprise (thỏa thuận riêng) |
| Google STT | tốt | ~$0.96/giờ, giảm theo volume | ✗ |
| SenseVoice (Alibaba, OSS) | Trung tốt hơn Whisper | free | ✓ |

Self-host faster-whisper: ~25–30× realtime trên GPU; ~$0.013–0.032/giờ audio trên GPU thuê — rẻ hơn API 10–30× ở volume lớn (cộng chi phí vận hành). **Lưu ý:** giọng người học (L2) cho WER cao hơn benchmark — cần pilot với audio học sinh thật.

## 3. LLM chấm Writing — bằng chứng & giới hạn

**Bằng chứng ủng hộ:**
- ChatGPT chấm IELTS Writing Task 2 trên 56 bài mẫu Cambridge: **QWK 0.811** so với examiner ([ERIC EJ1457168](https://files.eric.ed.gov/fulltext/EJ1457168.pdf)).
- GPT-4 chấm placement test (TESOL Quarterly 2025, 300 bài): quyết định xếp lớp đồng thuận tốt hơn mức trung bình giữa các giám khảo người ([Wiley](https://onlinelibrary.wiley.com/doi/10.1002/tesq.3405)).
- Tổng hợp 65 nghiên cứu 2022–2025: đồng thuận LLM–người moderate-to-good (QWK 0.30–0.80, dao động lớn theo model/prompt/dataset).
- Vòng lặp reflect-and-revise rubric trên dữ liệu điểm GV: QWK tăng tới +0.19–0.47 ([arXiv 2510.09030](https://arxiv.org/abs/2510.09030)) → dữ liệu (điểm AI, điểm GV) của chính hệ thống là tài sản hiệu chuẩn.

**Giới hạn đã ghi nhận (lý do phải hybrid):**
1. Central tendency bias — né điểm cực trị, dồn điểm về giữa.
2. Bias theo L1 — sai số tăng khi model nhận ra người viết non-native.
3. Length bias — thiên vị bài dài.
4. Nghiêm khắc hệ thống ở rubric analytic.
5. Nhạy với prompt/temperature — kết quả dao động giữa các lần chạy.

**Kỹ thuật prompt đã kiểm chứng:** band descriptor chính thức từng tiêu chí; chấm analytic từng tiêu chí trước rồi tổng hợp; few-shot 2–3 bài mẫu có điểm chuẩn; rationale trước điểm (CoT) + JSON; temperature 0, chấm 2–3 lần lấy median.

## 4. TTS tạo bài nghe

| Dịch vụ | Giá | 4 ngôn ngữ | Ghi chú |
|---|---|---|---|
| **Azure Neural TTS** | $16/1M ký tự (HD $22) | ✓ giọng bản xứ | Mặc định — SSML chỉnh tốc độ theo trình độ |
| Google TTS | $4–30/1M tùy loại | ✓ | Thay thế tương đương |
| ElevenLabs | ~$100/1M | ✓ (29+ ngôn ngữ) | Tự nhiên nhất, đắt ~6× — dùng chọn lọc |
| OpenAI TTS | ~$15/1M quy đổi | Giọng thiên tiếng Anh | Kém phù hợp bài nghe CJK |

Bài nghe sinh 1 lần rồi cache/tái sử dụng → chi phí TTS phân bổ/học sinh ≈ 0.

## 5. Chi phí ước tính / học sinh / tháng

Giả định: 20 bài speaking × 1 phút + 4 bài writing × 250 từ.

| Cấu hình | Chi phí |
|---|---|
| Scripted speaking (Azure PA) + writing model nhỏ | **≈ $0.3–0.5** (~8–13k VNĐ) |
| Unscripted speaking + writing model lớn | ≈ $1.7–2.5 (~45–65k VNĐ) |

→ Nhỏ so với học phí (1,7–4,7tr/tháng); ở quy mô lớn cần thương lượng enterprise tier. Quota AI theo gói ([SRS Gói dịch vụ](../14-goi-dich-vu/srs-goi-dich-vu.md)) phản ánh chi phí này.

## 6. Phương án on-premise

| Thành phần | Giải pháp | Đánh giá |
|---|---|---|
| STT | faster-whisper large-v3 (+ SenseVoice cho tiếng Trung); 1 GPU RTX 4090/L40S gánh 30–60 stream | Trưởng thành, rủi ro thấp |
| Chấm phát âm | **Không có OSS production-grade tương đương Azure**; hướng Kaldi GOP/wav2vec2 = R&D | Đề xuất: on-premise bỏ chỉ số phoneme, chấm fluency/nội dung từ transcript local; hoặc lai — chỉ tính năng phát âm gọi cloud |
| Chấm writing | LLM mở qua vLLM (Qwen-class) | Khả thi; chất lượng thấp hơn — GV review kỹ hơn |
| TTS | CosyVoice/Piper... | Cần PoC + thẩm định license — chưa đủ dữ liệu tin cậy cho CJK |
| Hạ tầng | 1–2 GPU server; LLM lớn cần A100-class | CAPEX vài trăm triệu VNĐ |

**Trade-off này phải ghi rõ trong hợp đồng on-premise** (đã phản ánh ở [Multi-tenant §6](../01-kien-truc/02-multi-tenant.md) và FR-GRADE-15).

## 7. Pattern tích hợp (đã phản ánh vào SRS Chấm bài)

Async queue; idempotency theo submission id; retry backoff 3–5 lần; circuit breaker; timeout job 5' → re-queue; degrade về GV chấm tay sau N giờ; lưu audio + transcript + raw JSON phục vụ audit/khiếu nại/hiệu chuẩn; cache TTS theo hash nội dung.

## Khoảng trống cần làm việc với vendor

Giá enterprise của ELSA/SpeechAce/Language Confidence; Azure disconnected container; định nghĩa "request" của SpeechSuper với audio dài.

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tổng hợp từ web research | Claude |
| 2026-07-16 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
