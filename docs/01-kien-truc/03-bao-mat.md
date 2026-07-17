# Bảo mật dữ liệu

**Trạng thái:** 🟢 Đã chốt

> Yêu cầu từ chủ sản phẩm: **bảo mật dữ liệu tuyệt đối**. Hệ thống lưu dữ liệu cá nhân của trẻ vị thành niên (học sinh) → chuẩn bảo mật đặt ở mức cao nhất khả thi, tuân thủ **Nghị định 13/2023/NĐ-CP** về bảo vệ dữ liệu cá nhân.

## 1. Phân loại dữ liệu

| Mức | Dữ liệu | Yêu cầu |
|---|---|---|
| P1 — Nhạy cảm cao | Mật khẩu (hash), token, thông tin cá nhân học sinh (họ tên, ngày sinh, SĐT phụ huynh), audio giọng nói học sinh | Mã hóa at-rest, truy cập theo need-to-know, audit mọi truy cập bất thường |
| P2 — Nội bộ tenant | Điểm số, bài làm, nhận xét, báo cáo, nội dung tự soạn của tenant | RLS cách ly tenant, phân quyền theo vai trò trong tenant |
| P3 — Dùng chung | Kho nội dung global, cấu hình public (logo, tên trung tâm) | Kiểm soát ghi; đọc theo gói |

## 2. Xác thực (Authentication)

- Đăng nhập bằng **email/username + mật khẩu**; mật khẩu hash **Argon2id**; policy: ≥ 8 ký tự, kiểm tra chống mật khẩu phổ biến.
- **JWT access token ngắn hạn (15 phút) + refresh token xoay vòng (rotating, 30 ngày)** lưu httpOnly cookie `Secure; SameSite=Lax`. Phát hiện refresh token bị dùng lại → thu hồi cả chuỗi phiên.
- **Bắt buộc 2FA (TOTP)** với vai trò platform (`admin`, `content_editor`, `support_agent`) và tùy chọn bật cho `owner`, `manager`, `teacher`; khuyến nghị nổi bật với `owner` và `it_admin`; owner có thể ép buộc 2FA cho các vai trò quản lý của tenant mình.
- Chống brute-force: rate limit theo IP + tài khoản, khóa tạm sau 10 lần sai, CAPTCHA từ lần sai thứ 5.
- Học sinh nhỏ tuổi: tài khoản do trung tâm cấp, không yêu cầu email riêng (username + mật khẩu cấp phát, buộc đổi lần đầu).
- Phiên: đăng xuất từ xa (xem danh sách thiết bị), phiên hết hạn khi đổi mật khẩu.

## 3. Phân quyền (Authorization)

- **RBAC 11 vai trò** kiểm tra ở **tầng API** (decorator/dependency per-endpoint) — không tin frontend; chi tiết ma trận ở [SRS Phân quyền](../02-phan-quyen/srs-phan-quyen.md).
- **Cách ly tenant 2 lớp**: RLS ở DB + filter tường minh ở repository ([Multi-tenant](02-multi-tenant.md)).
- **Cách ly trong tenant**: giáo viên chỉ thấy lớp mình dạy; trợ giảng chỉ thấy lớp được gán; học sinh chỉ thấy dữ liệu của mình; phụ huynh chỉ thấy dữ liệu kết quả của con được liên kết; manager/it_admin/academic_head bị giới hạn theo phạm vi chi nhánh/tổ được gán; quyền trung tâm chỉ thuộc owner.
- Nguyên tắc **deny-by-default**: endpoint không khai báo quyền → từ chối.

## 4. Mã hóa

| Vị trí | Biện pháp |
|---|---|
| In-transit | TLS 1.2+ toàn bộ (kể cả nội bộ app ↔ MinIO/DB trong môi trường production); HSTS |
| At-rest — DB | Mã hóa volume/disk (LUKS hoặc encryption của cloud); cột nhạy cảm đặc biệt (SĐT phụ huynh) mã hóa mức ứng dụng (AES-256-GCM, key qua KMS/ENV tách biệt) |
| At-rest — Object storage | SSE (server-side encryption) của MinIO/S3/R2 |
| Backup | Mã hóa trước khi đưa ra khỏi máy chủ (age/gpg), key quản lý riêng |
| Secrets | Không hardcode; nạp qua ENV/secret manager; xoay vòng được; không log secrets |

## 5. Bảo vệ tầng ứng dụng

- **Upload file**: kiểm MIME thật (magic bytes) + đuôi + kích thước theo loại; file Office/PDF không thực thi; video/audio transcode qua worker cách ly; quét virus (ClamAV) với file tài liệu; phục vụ qua **presigned URL có hạn** — không bao giờ public bucket.
- **Chống tấn công phổ biến**: SQL injection (chỉ query tham số hóa qua SQLAlchemy/asyncpg), XSS (React escape mặc định + CSP nghiêm; nội dung rich-text sanitize server-side bằng allowlist), CSRF (SameSite cookie + double-submit token cho thao tác ghi), SSRF (worker không fetch URL người dùng nhập trừ allowlist), IDOR (mọi truy vấn theo id đều kèm điều kiện quyền).
- **Rate limiting** theo user + IP + endpoint (đặc biệt: đăng nhập, nộp bài, xin presigned URL, gọi AI).
- **Headers**: CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy.
- Dependencies: quét lỗ hổng định kỳ (pip-audit, npm audit) trong CI.

## 6. Audit log

Bất biến (append-only, không API sửa/xóa), lưu ≥ 2 năm. Đây là tầng **nhạy cảm**; tầng rộng hơn — activity log ghi *mọi* thao tác ghi của mọi module (ai sửa gì, before/after) + UI quản trị — đặc tả ở [SRS Quản trị log](../18-quan-tri-log/srs-quan-tri-log.md):

| Nhóm sự kiện | Ví dụ |
|---|---|
| Truy cập nhạy cảm | Đăng nhập/thất bại, đổi mật khẩu, bật/tắt 2FA, impersonation (bắt đầu/kết thúc, ticket liên quan) |
| Thay đổi dữ liệu trọng yếu | Sửa điểm sau khi chốt, xóa lớp/học sinh, đổi vai trò, đổi gói/quota |
| Xuất dữ liệu | Xuất báo cáo, export danh sách học sinh |
| Cấu hình | Đổi cấu hình tenant, kênh thông báo, AI provider |

Mỗi bản ghi: `who, role, tenant, action, target, before/after (nếu áp dụng), ip, user_agent, at`.

## 7. Tuân thủ Nghị định 13/2023/NĐ-CP (bảo vệ dữ liệu cá nhân)

- **Đồng ý xử lý dữ liệu**: khi trung tâm tạo tài khoản học sinh, hệ thống cung cấp mẫu thông báo xử lý dữ liệu cá nhân để trung tâm lấy đồng ý từ phụ huynh/học sinh (trách nhiệm pháp lý chia sẻ: Edmicro là bên xử lý, trung tâm là bên kiểm soát — ghi rõ trong hợp đồng).
- **Quyền chủ thể dữ liệu**: xuất dữ liệu cá nhân của 1 học sinh (data portability), xóa/ẩn danh hóa khi kết thúc hợp đồng theo yêu cầu (soft-delete 30 ngày → anonymize: giữ số liệu thống kê, xóa danh tính).
- **Lưu trú dữ liệu**: dữ liệu SaaS lưu tại server đặt ở Việt Nam (yêu cầu hạ tầng — ghi ở [Vận hành](07-van-hanh-trien-khai.md)).
- **Data retention**: bài audio/video của học sinh giữ tối đa theo cấu hình tenant (mặc định 24 tháng) rồi tự xóa; điểm số giữ theo hợp đồng.
- **Hồ sơ DPIA**: Edmicro lập và nộp hồ sơ đánh giá tác động xử lý dữ liệu cá nhân (DPIA) cho nền tảng theo quy định; cung cấp **bộ tài liệu mẫu** (mô tả hệ thống, luồng dữ liệu, biện pháp bảo vệ) để trung tâm đính kèm khi tự lập DPIA của mình với vai trò bên kiểm soát.
- **Gửi AI bên thứ ba**: bài làm gửi đi chấm được **ẩn danh** (không kèm tên/ID thật của học sinh); ghi rõ danh sách sub-processor trong hợp đồng; on-premise có phương án AI local.

## 8. Ứng phó sự cố

- Phát hiện: cảnh báo đăng nhập bất thường, spike lỗi 403/401, truy cập audit log.
- Quy trình: cô lập → đánh giá phạm vi → thông báo khách hàng bị ảnh hưởng trong 72h → báo cáo cơ quan chức năng theo NĐ 13 khi cấu thành sự cố dữ liệu cá nhân → post-mortem.
- Diễn tập khôi phục backup tối thiểu mỗi quý ([Vận hành](07-van-hanh-trien-khai.md)).

## 9. Câu hỏi mở cần chốt

| # | Câu hỏi | Quyết định | Ngày chốt |
|---|---|---|---|
| 1 | Có thuê pentest độc lập trước go-live không? (khuyến nghị: có) | **Chốt:** Có — pentest độc lập trước go-live và sau mỗi thay đổi lớn về auth | 2026-07-16 |
| 2 | KMS dùng gì ở SaaS (Vault self-host / KMS của cloud VN)? | **Chốt:** Vault self-host (chạy được cả SaaS lẫn on-premise, không phụ thuộc cloud) | 2026-07-16 |
| 3 | Mức retention audio mặc định 24 tháng — OK? | **Chốt:** 24 tháng, cấu hình được per tenant | 2026-07-16 |

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo bản nháp đầu tiên | Claude |
| 2026-07-16 | Chốt toàn bộ câu hỏi mở (quyết định ghi trong bảng), chuyển trạng thái Đã chốt | Chủ sản phẩm |
| 2026-07-16 | RBAC 11 vai trò; bổ sung cách ly theo phạm vi chi nhánh/tổ và phụ huynh | Chủ sản phẩm |
| 2026-07-17 | Bổ sung mục hồ sơ DPIA (phát hiện thiếu khi tổng rà soát) | Chủ sản phẩm + Claude |
| 2026-07-17 | Liên kết audit log với module LOG mới | Chủ sản phẩm + Claude |
