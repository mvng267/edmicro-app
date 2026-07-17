# Thuật ngữ (Glossary)

**Trạng thái:** 🟢 Đã chốt

> Mọi tài liệu và code dùng thống nhất thuật ngữ dưới đây. Tên tiếng Anh dùng cho entity/API/code; tên tiếng Việt dùng trên UI và trong docs.

## Tổ chức & người dùng

| Tiếng Anh (code/entity) | Tiếng Việt (UI/docs) | Định nghĩa |
|---|---|---|
| Tenant | Trung tâm | Một trung tâm ngoại ngữ — đơn vị khách hàng B2B, ranh giới cách ly dữ liệu |
| Branch | Chi nhánh | Cơ sở vật lý của trung tâm (1 tenant có ≥1 chi nhánh) |
| Class | Lớp học | Nhóm học sinh học cùng nhau, thuộc 1 chi nhánh, có giáo viên phụ trách |
| User | Người dùng | Tài khoản đăng nhập, thuộc 1 tenant (trừ vai trò platform) |
| Role | Vai trò | Nhóm quyền gán cho user — xem [Phân quyền](../02-phan-quyen/srs-phan-quyen.md) |

## Vai trò (11 vai trò)

> Tách rõ 2 nhóm quyền quản lý trong tenant: **quyền trung tâm** (`owner` — sở hữu, cấu hình, hợp đồng) và **quyền nhân viên quản lý** (`manager` — vận hành học vụ hằng ngày). `owner` có mọi quyền của `manager`; chiều ngược lại thì không.

| Mã role | Tiếng Việt | Cấp | Ghi chú |
|---|---|---|---|
| `admin` | Admin hệ thống | Platform | Nhân sự vận hành nền tảng (Edmicro), quản lý tenant, gói dịch vụ |
| `content_editor` | Nhân viên nội dung | Platform | Soạn/cấu hình kho nội dung dùng chung, phân phối cho tenant |
| `support_agent` | Nhân viên support | Platform | Hỗ trợ người dùng, xử lý ticket, đăng nhập thay (có audit) |
| `owner` | Chủ trung tâm | Tenant | **Quyền trung tâm**: cấu hình trung tâm, kênh thông báo (Zalo OA/SMTP/SMS), chi nhánh, gói & usage, tạo tài khoản quản lý (`manager`/`it_admin`/`academic_head`), bật/tắt impersonation & gamification, audit log tenant. Tài khoản đầu tiên của tenant là owner |
| `manager` | Nhân viên quản lý (học vụ) | Tenant | **Quyền vận hành**: lớp, học sinh, giao bài, báo cáo, lịch học, thông báo — toàn trung tâm hoặc theo chi nhánh được gán |
| `academic_head` | Tổ trưởng chuyên môn | Tenant | Quyền teacher + duyệt nội dung tenant + xem báo cáo các lớp trong phạm vi tổ (theo ngôn ngữ giảng dạy, tùy chọn giới hạn chi nhánh) |
| `it_admin` | IT trung tâm | Tenant | Quản lý tài khoản (tạo, import, reset mật khẩu, khóa/mở) và phân lớp — toàn trung tâm hoặc theo chi nhánh được gán; **không** xem điểm số, bài làm, báo cáo học tập |
| `teacher` | Giáo viên / Giảng viên | Tenant | Dạy lớp, soạn bài, giao bài, chấm bài, xem báo cáo lớp mình |
| `assistant` | Trợ giảng | Tenant | Hỗ trợ giáo viên: chấm bài được ủy quyền, điểm danh, nhắc học sinh |
| `student` | Học sinh | Tenant | Học khóa học, làm practice/exam, xem kết quả của mình |
| `parent` | Phụ huynh | Tenant | Xem báo cáo học tập, lịch học, chuyên cần của con (liên kết 1+ học sinh); nhận thông báo. Không xem nội dung bài học/đề thi |

**Phạm vi chi nhánh (branch scope):** `manager` và `it_admin` được gán phạm vi *toàn trung tâm* hoặc *1+ chi nhánh cụ thể*; `academic_head` gán theo *ngôn ngữ giảng dạy* (tùy chọn kèm chi nhánh). Quyền chỉ có hiệu lực trong phạm vi được gán.

## Nội dung học tập

| Tiếng Anh | Tiếng Việt | Định nghĩa |
|---|---|---|
| Course | Khóa học | Chuỗi bài học có thứ tự; chứa lesson, nhúng được practice/exam |
| Lesson | Bài học | Một đơn vị học trong khóa học; chứa nhiều loại content block |
| Content Block | Khối nội dung | Thành phần trong bài học: video, văn bản, flashcard set, file tài liệu (Word/Excel/PPT/PDF), practice nhúng, exam nhúng |
| Flashcard Set | Bộ thẻ ghi nhớ | Tập thẻ 2 mặt (từ vựng/mẫu câu) học theo spaced repetition |
| Practice | Bài luyện tập | Bài tập theo kỹ năng: Nghe (Listening), Nói (Speaking), Đọc (Reading), Viết (Writing) |
| Exam | Bài thi thử | Đề thi mô phỏng kỳ thi chuẩn (IELTS, TOEIC, VSTEP, HSK, JLPT, TOPIK…), có giới hạn thời gian |
| Skill | Kỹ năng | Một trong bốn: `listening` / `speaking` / `reading` / `writing` |
| Question | Câu hỏi | Đơn vị nhỏ nhất của practice/exam; thuộc một Question Type |
| Question Type | Loại câu hỏi | Dạng tương tác của câu hỏi (trắc nghiệm, điền từ, ghi âm…) — catalog ở [Phụ lục](../99-phu-luc/01-loai-cau-hoi.md) |
| Question Bank | Ngân hàng câu hỏi | Kho câu hỏi có tag (ngôn ngữ, kỹ năng, level, chủ đề) để tái sử dụng |
| Section | Phần thi | Nhóm câu hỏi trong exam theo cấu trúc kỳ thi thật (VD: IELTS Listening Part 1) |
| Language | Ngôn ngữ giảng dạy | Ngôn ngữ mà nội dung dạy (en, zh, ja, ko…) — hệ thống ngôn ngữ-agnostic |
| Level | Trình độ | Mức của nội dung, map về CEFR hoặc thang riêng của kỳ thi (HSK 1–6, N5–N1…) |

## Giao bài & làm bài

| Tiếng Anh | Tiếng Việt | Định nghĩa |
|---|---|---|
| Assignment | Lượt giao bài | Hành động giao 1 nội dung (course/practice/exam) cho đối tượng (lớp/nhóm/cá nhân) kèm deadline |
| Assignee | Người được giao | Học sinh nằm trong phạm vi của assignment |
| Attempt | Lượt làm bài | Một lần học sinh làm 1 practice/exam (có thể cho phép nhiều attempt) |
| Submission | Bài nộp | Kết quả cuối của một attempt, gồm các câu trả lời (answer) |
| Answer | Câu trả lời | Trả lời của học sinh cho 1 câu hỏi (text, lựa chọn, file audio…) |
| Deadline | Hạn nộp | Thời hạn của assignment; sau hạn có thể cho nộp muộn (đánh dấu `late`) |

## Chấm bài & báo cáo

| Tiếng Anh | Tiếng Việt | Định nghĩa |
|---|---|---|
| Auto Grading | Chấm tự động | Chấm bằng đáp án (trắc nghiệm, điền từ…) — kết quả ngay |
| AI Grading | Chấm AI | AI chấm sơ bộ speaking/writing theo rubric, trả điểm + nhận xét đề xuất |
| Review | Duyệt chấm | Giáo viên/trợ giảng xem lại kết quả AI, sửa điểm/nhận xét và chốt |
| Rubric | Thang chấm | Bộ tiêu chí chấm theo chuẩn kỳ thi (VD: IELTS Writing: TA, CC, LR, GRA) |
| Final Score | Điểm chốt | Điểm sau khi giáo viên duyệt — điểm chính thức dùng cho báo cáo |
| Report | Báo cáo | Tổng hợp kết quả học tập theo cấp: học sinh → lớp → giáo viên → trung tâm |

## Vận hành

| Tiếng Anh | Tiếng Việt | Định nghĩa |
|---|---|---|
| Notification | Thông báo | Tin nhắn hệ thống gửi qua kênh: in-app, email, Zalo OA/SMS |
| Session | Buổi học | Một buổi trên thời khóa biểu của lớp |
| Attendance | Điểm danh | Ghi nhận có mặt/vắng/muộn của học sinh theo buổi học |
| Points / Streak / Badge / Leaderboard | Điểm thưởng / Chuỗi ngày học / Huy hiệu / Bảng xếp hạng | Thành phần gamification |
| Plan | Gói dịch vụ | Gói mà tenant đăng ký, quy định hạn mức (quota) |
| Quota | Hạn mức | Giới hạn theo gói: số học sinh active, dung lượng file, lượt chấm AI/tháng |
| Ticket | Yêu cầu hỗ trợ | Yêu cầu người dùng gửi cho support |
| Impersonation | Đăng nhập thay | Support đăng nhập với tư cách người dùng khác để hỗ trợ — luôn ghi audit log |
| Audit Log | Nhật ký hệ thống | Bản ghi bất biến các hành động **nhạy cảm** (ai, làm gì, lúc nào, từ đâu) — tập con nghiêm ngặt của Activity Log |
| Activity Log | Nhật ký hoạt động | Bản ghi **mọi thao tác ghi** trên mọi module: ai sửa gì, before/after — xem [SRS Quản trị log](../18-quan-tri-log/srs-quan-tri-log.md) |

## Quy ước đặt mã

- Mã module (dùng trong FR/US): `AUTH`(phân quyền) `ORG`(tổ chức) `COURSE` `PRACTICE` `EXAM` `ASSIGN` `GRADE` `REPORT` `CONTENT` `NOTIF` `SCHED` `GAME` `PLAN` `SUPPORT` `LOG`(nhật ký hoạt động)
- Yêu cầu chức năng: `FR-<MODULE>-<số 2 chữ số>` — VD `FR-GRADE-04`
- User story: `US-<MODULE>-<số>` — VD `US-EXAM-02`

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo bản nháp đầu tiên | Claude |
| 2026-07-16 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
| 2026-07-16 | Tách quyền trung tâm (`owner`) khỏi nhân viên quản lý (`manager`); thêm `academic_head`, `parent`; phạm vi chi nhánh — 11 vai trò | Chủ sản phẩm |
| 2026-07-17 | Thêm module LOG + thuật ngữ Activity Log | Chủ sản phẩm + Claude |
