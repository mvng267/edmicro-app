# Tài liệu sản phẩm — Edmicro App

> LMS B2B đa ngôn ngữ cho trung tâm ngoại ngữ tại Việt Nam.
> Bộ tài liệu này là **nguồn chân lý duy nhất** để chốt sản phẩm trước khi implement.

## Cách đọc

- Đọc theo thứ tự: `00-tong-quan` → `01-kien-truc` → các module `02`–`15` → `16-du-lieu` → `17-mockups`.
- Mỗi module nghiệp vụ có 1 file SRS theo template chung: [\_template-srs.md](_template-srs.md).
- Yêu cầu chức năng đánh số `FR-<MODULE>-<số>` (VD: `FR-EXAM-03`) — dùng mã này khi trao đổi/chốt.
- Mockup màn hình: mở file `.html` trong [17-mockups/](17-mockups/) trực tiếp bằng browser.
- Trạng thái chốt: 🟡 Nháp → 🔵 Chờ chốt → 🟢 Đã chốt.

## Mục lục & trạng thái

| # | Tài liệu | Nội dung | Trạng thái |
|---|---|---|---|
| — | [Template SRS](_template-srs.md) | Template chung cho mọi module | 🟢 Đã chốt |
| 00 | [Tầm nhìn sản phẩm](00-tong-quan/01-tam-nhin-san-pham.md) | Vision, USP, phạm vi v1/v2 | 🟢 Đã chốt |
| 00 | [Nghiên cứu thị trường](00-tong-quan/02-nghien-cuu-thi-truong.md) | Ngành ngoại ngữ VN, đối thủ, khoảng trống | 🟢 Đã chốt |
| 00 | [Personas](00-tong-quan/03-personas.md) | Chân dung 11 vai trò người dùng | 🟢 Đã chốt |
| 00 | [Thuật ngữ](00-tong-quan/04-thuat-ngu.md) | Glossary dùng thống nhất toàn bộ docs | 🟢 Đã chốt |
| 00 | [Luồng nghiệp vụ chính](00-tong-quan/05-luong-nghiep-vu-chinh.md) | Truy vết yêu cầu gốc → 4 luồng xuyên suốt → FR | 🟢 Đã chốt |
| 01 | [Kiến trúc tổng thể](01-kien-truc/01-kien-truc-tong-the.md) | C4, tech stack, quyết định kỹ thuật | 🟢 Đã chốt |
| 01 | [Multi-tenant](01-kien-truc/02-multi-tenant.md) | Tenant, RLS, SaaS vs on-premise | 🟢 Đã chốt |
| 01 | [Bảo mật](01-kien-truc/03-bao-mat.md) | Yêu cầu bảo mật dữ liệu tuyệt đối | 🟢 Đã chốt |
| 01 | [Lưu trữ file](01-kien-truc/04-luu-tru-file.md) | Storage adapter MinIO → S3/R2 | 🟢 Đã chốt |
| 01 | [Cấu trúc code](01-kien-truc/05-cau-truc-code.md) | Quy ước chia module backend/frontend | 🟢 Đã chốt |
| 01 | [Phi chức năng](01-kien-truc/06-yeu-cau-phi-chuc-nang.md) | Hiệu năng, uptime, backup, i18n | 🟢 Đã chốt |
| 01 | [Vận hành & triển khai](01-kien-truc/07-van-hanh-trien-khai.md) | Deploy SaaS + on-premise, CI/CD | 🟢 Đã chốt |
| 02 | [Phân quyền](02-phan-quyen/srs-phan-quyen.md) | Ma trận RBAC 11 vai trò | 🟢 Đã chốt |
| 03 | [Tổ chức & người dùng](03-to-chuc-nguoi-dung/srs-to-chuc-nguoi-dung.md) | Tenant, chi nhánh, lớp, user lifecycle | 🟢 Đã chốt |
| 04 | [Khóa học](04-khoa-hoc/srs-khoa-hoc.md) | Bài học, video, flashcard, file, nhúng practice/exam | 🟢 Đã chốt |
| 05 | [Practice](05-practice/srs-practice.md) | 4 kỹ năng nghe-nói-đọc-viết | 🟢 Đã chốt |
| 06 | [Exam](06-exam/srs-exam.md) | Thi thử theo chuẩn quốc tế | 🟢 Đã chốt |
| 07 | [Giao bài](07-giao-bai/srs-giao-bai.md) | Gán bài cho lớp/nhóm/cá nhân, deadline | 🟢 Đã chốt |
| 08 | [Chấm bài](08-cham-bai/srs-cham-bai.md) | Hybrid: AI chấm sơ bộ → GV review | 🟢 Đã chốt |
| 09 | [Báo cáo](09-bao-cao/srs-bao-cao.md) | Báo cáo đa cấp HS/lớp/GV/BGH | 🟢 Đã chốt |
| 10 | [Nội dung](10-noi-dung/srs-noi-dung.md) | Ngân hàng câu hỏi, quy trình duyệt | 🟢 Đã chốt |
| 11 | [Thông báo](11-thong-bao/srs-thong-bao.md) | In-app, email, Zalo OA/SMS | 🟢 Đã chốt |
| 12 | [Lịch học & điểm danh](12-lich-hoc-diem-danh/srs-lich-hoc-diem-danh.md) | Thời khóa biểu, điểm danh | 🟢 Đã chốt |
| 13 | [Gamification](13-gamification/srs-gamification.md) | Điểm thưởng, streak, xếp hạng | 🟢 Đã chốt |
| 14 | [Gói dịch vụ](14-goi-dich-vu/srs-goi-dich-vu.md) | Gói tenant, hạn mức, quota AI | 🟢 Đã chốt |
| 15 | [Hỗ trợ](15-ho-tro/srs-ho-tro.md) | Ticket, đăng nhập thay, tra cứu | 🟢 Đã chốt |
| 18 | [Quản trị log](18-quan-tri-log/srs-quan-tri-log.md) | Activity log mọi thao tác (ai sửa gì) + UI quản trị theo module | 🟢 Đã chốt |
| 16 | [ERD](16-du-lieu/01-erd.md) | Mô hình dữ liệu tổng | 🟢 Đã chốt |
| 16 | [Từ điển dữ liệu](16-du-lieu/02-tu-dien-du-lieu.md) | Data dictionary entity chính | 🟢 Đã chốt |
| 16 | [Danh mục bảng](16-du-lieu/03-danh-muc-bang.md) | Toàn bộ ~70 bảng theo module — checklist migration | 🟢 Đã chốt |
| 17 | [Mockups](17-mockups/README.md) | 16 màn hình HTML theo HeroUI | 🟢 Đã chốt |
| 99 | [Loại câu hỏi](99-phu-luc/01-loai-cau-hoi.md) | Catalog ~24 loại câu hỏi theo kỹ năng | 🟢 Đã chốt |
| 99 | [Chuẩn thi quốc tế](99-phu-luc/02-chuan-thi-quoc-te.md) | Format kỳ thi + CEFR mapping | 🟢 Đã chốt |
| 99 | [Nghiên cứu AI chấm bài](99-phu-luc/03-nghien-cuu-ai-cham-bai.md) | Vendor, giá, độ tin cậy, on-premise | 🟢 Đã chốt |

## Quy ước chung

- **Ngôn ngữ tài liệu**: tiếng Việt; tên module, entity, API bằng tiếng Anh (xem [Thuật ngữ](00-tong-quan/04-thuat-ngu.md)).
- **Sơ đồ**: mermaid (flowchart cho luồng nghiệp vụ, sequence cho tương tác hệ thống, erDiagram cho dữ liệu).
- **Thay đổi sau khi đã chốt** (🟢): phải ghi vào mục "Lịch sử thay đổi" cuối file tương ứng.
