# Yêu cầu phi chức năng (NFR)

**Trạng thái:** 🟢 Đã chốt

> NFR chung toàn hệ thống. NFR riêng của từng module ghi ở mục 7 trong SRS module đó.

## 1. Hiệu năng

| Mã | Yêu cầu | Mục tiêu |
|---|---|---|
| NFR-PERF-01 | Thời gian phản hồi API (p95) cho thao tác đọc thường | < 300ms |
| NFR-PERF-02 | Thời gian phản hồi API (p95) cho thao tác ghi (nộp câu trả lời) | < 500ms |
| NFR-PERF-03 | **Thi đồng thời**: 1 tenant tổ chức thi thử với 500 học sinh cùng lúc (SaaS tổng: 2.000 phiên thi đồng thời) — nộp từng câu không mất dữ liệu | Không lỗi, p95 < 1s |
| NFR-PERF-04 | Tải trang đầu (LCP) trên mobile 4G | < 3s |
| NFR-PERF-05 | Kết quả chấm AI trả về cho học sinh (từ lúc nộp) | p90 < 3 phút |
| NFR-PERF-06 | Báo cáo tenant lớn (5.000 học sinh) render dashboard | < 5s (pre-aggregate, không tính realtime) |

**Chiến lược đáp ứng NFR-PERF-03 (thi đồng thời)** — rủi ro hiệu năng lớn nhất:
- Nộp bài theo **từng câu** (autosave) chứ không nộp cả bài 1 lần → tải dàn đều, mất kết nối không mất bài.
- Đề thi (câu hỏi + media) được cache/CDN-hóa qua presigned URL dài hạn cho kỳ thi; API chỉ nhận answer.
- Answer ghi qua hàng đợi in-memory batch → Postgres (hoặc ghi thẳng với batch insert), đo bằng load test trước go-live.
- Load test là điều kiện release: kịch bản 500 HS thi 60 phút, xem [Vận hành](07-van-hanh-trien-khai.md).

## 2. Khả dụng & độ tin cậy

| Mã | Yêu cầu | Mục tiêu |
|---|---|---|
| NFR-AVAIL-01 | Uptime SaaS (ngoài bảo trì có báo trước) | ≥ 99,5%/tháng |
| NFR-AVAIL-02 | RPO (mất dữ liệu tối đa khi sự cố) | ≤ 15 phút (WAL archiving) |
| NFR-AVAIL-03 | RTO (thời gian khôi phục) | ≤ 4 giờ |
| NFR-AVAIL-04 | Bài đang làm không mất khi mất mạng tạm thời | Autosave local + retry; khôi phục phiên làm bài |
| NFR-AVAIL-05 | AI service lỗi/quá tải | Bài vào hàng đợi chờ, học sinh thấy trạng thái "đang chấm"; GV vẫn chấm tay được (degrade có kiểm soát) |

## 3. Quy mô thiết kế (capacity)

| Chiều | v1 thiết kế cho | Ghi chú |
|---|---|---|
| Tenant (SaaS) | 200 trung tâm | |
| Học sinh / tenant | 5.000 (lớn nhất); điển hình 300–1.500 | |
| Tổng user | ~500.000 tài khoản (gồm tài khoản phụ huynh ~1/học sinh, tần suất dùng thấp) | |
| Lưu trữ file | 50 GB–2 TB / tenant theo gói | |
| Lượt chấm AI | 500.000 lượt/tháng toàn hệ thống | Queue scale ngang bằng thêm worker |

## 4. Bảo mật

Xem [Bảo mật](03-bao-mat.md) — là một phần của NFR, tách doc riêng vì yêu cầu "tuyệt đối".

## 5. i18n & l10n

| Mã | Yêu cầu |
|---|---|
| NFR-I18N-01 | UI mặc định tiếng Việt; kiến trúc string qua next-intl, thêm locale (en) không sửa code |
| NFR-I18N-02 | **Nội dung học** hiển thị đúng mọi hệ chữ: Hán tự, kana + furigana, Hangul, IPA; font fallback chuẩn |
| NFR-I18N-03 | Audio/văn bản RTL: chưa hỗ trợ v1 (ghi nhận cho tiếng Ả Rập ở v2) |
| NFR-I18N-04 | Múi giờ theo tenant (mặc định Asia/Ho_Chi_Minh); deadline hiển thị theo múi giờ tenant |

## 6. Khả năng tiếp cận & tương thích

| Mã | Yêu cầu |
|---|---|
| NFR-COMPAT-01 | Trình duyệt: 2 phiên bản lớn gần nhất của Chrome, Safari, Edge, Firefox; Safari iOS ≥ 16 |
| NFR-COMPAT-02 | Giao diện học sinh: **mobile-first** (360px+); giao diện quản trị: tối ưu desktop, dùng được trên tablet |
| NFR-COMPAT-03 | Ghi âm (speaking) hoạt động trên Safari iOS và Chrome Android (MediaRecorder + fallback) |
| NFR-A11Y-01 | Đạt WCAG 2.1 mức AA cho luồng học sinh chính (làm bài, xem kết quả); HeroUI (React Aria) hỗ trợ sẵn phần lớn |
| NFR-A11Y-02 | Dark mode toàn hệ thống (HeroUI theme) |

## 7. Khả năng bảo trì & quan sát

| Mã | Yêu cầu |
|---|---|
| NFR-MAINT-01 | Structured logging (JSON) + correlation id xuyên request→job; log không chứa dữ liệu nhạy cảm |
| NFR-MAINT-02 | Metrics (Prometheus format): API latency, queue depth, tỉ lệ lỗi AI, quota usage; dashboard + alert |
| NFR-MAINT-03 | Error tracking (Sentry self-host hoặc tương đương, host tại VN) |
| NFR-MAINT-04 | Test coverage tối thiểu: service layer 80%; luồng E2E chính (làm bài, giao bài, chấm, báo cáo) có Playwright test |
| NFR-MAINT-05 | Migration DB luôn reversible hoặc có script rollback; zero-downtime với thay đổi thường |

## 8. Câu hỏi mở cần chốt

| # | Câu hỏi | Quyết định | Ngày chốt |
|---|---|---|---|
| 1 | Con số 500 HS thi đồng thời/tenant đã đủ cho khách mục tiêu chưa (chuỗi lớn có thể thi 2.000+)? | **Chốt:** Giữ 500 HS/tenant cho v1; kiến trúc scale ngang, load test lại theo hợp đồng khách chuỗi lớn | 2026-07-16 |
| 2 | Cam kết SLA trong hợp đồng B2B: 99,5% hay 99,9% (ảnh hưởng chi phí hạ tầng)? | **Chốt:** SLA chuẩn 99,5%; 99,9% chỉ theo thỏa thuận riêng có phụ phí | 2026-07-16 |

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo bản nháp đầu tiên | Claude |
| 2026-07-16 | Chốt toàn bộ câu hỏi mở (quyết định ghi trong bảng), chuyển trạng thái Đã chốt | Chủ sản phẩm |
| 2026-07-17 | Nâng capacity tổng user lên ~500k do thêm tài khoản phụ huynh v1 | Chủ sản phẩm + Claude |
