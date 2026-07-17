# Personas — Chân dung người dùng

**Trạng thái:** 🟢 Đã chốt

> 11 vai trò của hệ thống, chia 2 cấp: **Tenant** (người của trung tâm) và **Platform** (người vận hành nền tảng). Trong tenant, quyền quản lý tách 2 tầng: **quyền trung tâm** (`owner`) và **quyền nhân viên quản lý** (`manager`). Chi tiết quyền xem [SRS Phân quyền](../02-phan-quyen/srs-phan-quyen.md).

## Cấp Tenant (trung tâm ngoại ngữ)

### 1. Học sinh — `student`

**Đại diện:** Minh, 16 tuổi, học IELTS mục tiêu 6.5; Lan, 24 tuổi, học tiếng Nhật N3 để đi làm.

- **Bối cảnh dùng:** chủ yếu điện thoại (70–80%), buổi tối sau giờ học/làm; laptop khi làm bài thi thử dài.
- **Mục tiêu:** biết hôm nay phải làm gì (bài được giao, deadline), luyện 4 kỹ năng, thi thử sát đề thật, thấy tiến bộ của mình.
- **Đau điểm hiện tại:** bài tập giao qua Zalo/giấy dễ trôi, không biết mình yếu kỹ năng nào, chờ giáo viên chấm speaking/writing rất lâu.
- **Điều hệ thống phải làm tốt:** danh sách việc cần làm rõ ràng, làm bài mượt trên mobile, nhận phản hồi AI nhanh cho speaking/writing, xem lộ trình và tiến bộ trực quan, có động lực (điểm thưởng, streak, xếp hạng).

### 2. Phụ huynh — `parent`

**Đại diện:** Chị Hạnh, mẹ của Minh — người trả học phí và quyết định có tái ghi danh hay không.

- **Bối cảnh dùng:** điện thoại, vài phút buổi tối; quen dùng Zalo hơn app.
- **Mục tiêu:** biết con học có tiến bộ không, có đi học đầy đủ không, tiền học phí có xứng đáng không.
- **Đau điểm hiện tại:** chỉ nhận tin nhắn Zalo rời rạc từ trung tâm; muốn xem lại thì trôi mất; không có bức tranh tổng thể.
- **Điều hệ thống phải làm tốt:** đăng nhập đơn giản (tài khoản trung tâm cấp), xem báo cáo kết quả + chuyên cần + lịch học của con (nhiều con = 1 tài khoản), nhận thông báo quan trọng; **không** thấy nội dung đề/bài học (bảo vệ nội dung trung tâm).

### 3. Giáo viên / Giảng viên — `teacher`

**Đại diện:** Cô Hương, dạy 4 lớp IELTS ~60 học sinh; Thầy Tuấn, dạy tiếng Trung HSK 2 lớp.

- **Bối cảnh dùng:** laptop tại trung tâm và ở nhà; thời gian soạn bài + chấm bài ngoài giờ dạy rất hạn chế.
- **Mục tiêu:** giao bài cho cả lớp trong vài phút, chấm nhanh nhờ AI chấm sơ bộ, nắm ngay học sinh nào chưa làm/đang yếu để can thiệp.
- **Đau điểm hiện tại:** chấm speaking/writing thủ công tốn 5–15 phút/bài; tổng hợp điểm bằng Excel; không có dữ liệu hệ thống về từng học sinh.
- **Điều hệ thống phải làm tốt:** giao bài theo lớp/nhóm/cá nhân kèm deadline; hàng đợi chấm bài với điểm AI đề xuất sẵn — chỉ sửa và chốt; báo cáo lớp trực quan; tái sử dụng nội dung từ ngân hàng câu hỏi.

### 4. Trợ giảng — `assistant`

**Đại diện:** Bạn Quỳnh, sinh viên năm 3, trợ giảng 3 lớp.

- **Mục tiêu:** hỗ trợ giáo viên các việc lặp lại: điểm danh, nhắc học sinh làm bài, chấm phần được ủy quyền.
- **Đau điểm hiện tại:** nhắn tin nhắc từng học sinh qua Zalo, không rõ mình được quyền làm gì.
- **Điều hệ thống phải làm tốt:** phạm vi quyền rõ ràng theo lớp được gán; danh sách học sinh chưa nộp để nhắc 1-chạm; chấm bài trong phạm vi giáo viên ủy quyền (giáo viên vẫn là người chốt điểm cuối).

### 5. Tổ trưởng chuyên môn — `academic_head`

**Đại diện:** Thầy Long, tổ trưởng tổ tiếng Anh — 12 giáo viên, 30 lớp.

- **Bối cảnh dùng:** laptop; vừa dạy lớp của mình vừa quản chất lượng chuyên môn của tổ.
- **Mục tiêu:** nội dung tổ mình soạn ra phải đạt chuẩn trước khi đến học sinh; nhìn được chất lượng các lớp trong tổ để kèm giáo viên mới.
- **Đau điểm hiện tại:** đề tự soạn của giáo viên chất lượng không đều, không ai duyệt; không có số liệu so sánh giữa các lớp cùng level.
- **Điều hệ thống phải làm tốt:** hàng đợi duyệt nội dung của tổ (khi trung tâm bật "cần duyệt"); xem báo cáo + ngân hàng câu hỏi các lớp thuộc ngôn ngữ mình phụ trách; vẫn có đầy đủ quyền teacher với lớp mình dạy.

### 6. Nhân viên quản lý (học vụ) — `manager`

**Đại diện:** Chị Vy, trưởng phòng đào tạo phụ trách chi nhánh Quận 7 — xếp lớp, theo dõi chất lượng, làm việc với phụ huynh hằng ngày.

- **Bối cảnh dùng:** laptop tại văn phòng cả ngày — người dùng "nặng" nhất phía vận hành.
- **Mục tiêu:** vận hành trơn tru trong phạm vi được gán (toàn trung tâm hoặc chi nhánh): mở lớp, xếp giáo viên, theo dõi tỉ lệ hoàn thành bài, xử lý học sinh đuối, trả lời phụ huynh bằng số liệu.
- **Đau điểm hiện tại:** phải mượn tài khoản của chủ trung tâm để làm việc → thấy cả cấu hình, hợp đồng, những thứ không thuộc phận sự; chủ trung tâm thì lo bị sửa nhầm cấu hình.
- **Điều hệ thống phải làm tốt:** đủ quyền vận hành học vụ (lớp, học sinh, giao bài, báo cáo, lịch, thông báo) trong phạm vi chi nhánh được gán; **không** đụng được cấu hình trung tâm, kênh thông báo, gói dịch vụ.

### 7. Chủ trung tâm — `owner`

**Đại diện:** Cô Thảo, giám đốc trung tâm 3 chi nhánh, 40 giáo viên, 1.200 học sinh.

- **Bối cảnh dùng:** laptop + điện thoại; xem báo cáo hằng tuần, quyết định chiến lược theo quý.
- **Mục tiêu:** nhìn toàn cảnh chất lượng dạy–học của mọi chi nhánh; nắm phần "sở hữu": thương hiệu (logo/theme), kênh liên lạc (Zalo OA), gói dịch vụ & chi phí, ai được làm quản lý.
- **Đau điểm hiện tại:** tài khoản quản trị dùng chung với nhân viên — không phân biệt được ai làm gì, không dám giao tài khoản cho nhân viên mới.
- **Điều hệ thống phải làm tốt:** độc quyền cấu hình trung tâm + chi nhánh + kênh + xem gói/usage; tạo và gán phạm vi cho manager/it_admin/academic_head; xem audit log toàn tenant; kế thừa mọi quyền manager khi muốn tự vận hành.

### 8. IT trung tâm — `it_admin`

**Đại diện:** Anh Đức, nhân viên IT của chuỗi trung tâm 3 chi nhánh — người "cầm" toàn bộ tài khoản và thiết bị.

- **Bối cảnh dùng:** desktop tại văn phòng; cao điểm là đầu khóa học (tạo hàng loạt tài khoản, xếp lớp) và khi có sự cố đăng nhập.
- **Mục tiêu:** tạo/cấp phát tài khoản nhanh (import Excel), xếp học sinh vào đúng lớp, xử lý quên mật khẩu/khóa tài khoản trong vài phút mà không phải phiền ban quản lý.
- **Đau điểm hiện tại:** mọi việc tài khoản dồn lên quản lý hoặc giáo viên; không có vai trò kỹ thuật riêng nên IT phải mượn tài khoản quản lý — thấy cả điểm số, dữ liệu nhạy cảm không thuộc phận sự.
- **Điều hệ thống phải làm tốt:** đủ quyền quản lý tài khoản + phân lớp (import, reset mật khẩu, khóa/mở, chuyển lớp, gán GV/TA vào lớp) trong phạm vi chi nhánh được gán, nhưng **không thấy điểm số/bài làm/báo cáo học tập**; nhật ký thao tác rõ ràng để đối chiếu khi có khiếu nại.

## Cấp Platform (vận hành nền tảng)

### 9. Admin hệ thống — `admin`

**Đại diện:** Nhân sự vận hành của Edmicro.

- **Mục tiêu:** tạo/tạm ngưng tenant, gán gói dịch vụ và hạn mức, theo dõi sức khỏe hệ thống và mức dùng quota (đặc biệt chi phí AI), quản lý tài khoản platform.
- **Điều hệ thống phải làm tốt:** màn hình quản trị tenant + gói; cảnh báo vượt quota; audit log đầy đủ; không bao giờ thấy nội dung dữ liệu học tập của tenant khi không cần thiết (nguyên tắc least privilege).

### 10. Nhân viên nội dung — `content_editor`

**Đại diện:** Đội ngũ học thuật của Edmicro soạn kho đề dùng chung.

- **Mục tiêu:** xây kho nội dung chuẩn (câu hỏi, practice, đề thi thử theo format IELTS/TOEIC/HSK/JLPT/TOPIK/VSTEP) và phân phối cho các tenant theo gói.
- **Đau điểm hiện tại (công cụ cũ):** soạn đề trong Word rồi nhập tay; không quản lý được phiên bản và chất lượng.
- **Điều hệ thống phải làm tốt:** trình soạn câu hỏi theo từng loại (kể cả audio cho listening, prompt cho speaking); quy trình nháp → duyệt → xuất bản; tag theo ngôn ngữ/kỹ năng/level/chủ đề; import từ file có sẵn.

### 11. Nhân viên support — `support_agent`

**Đại diện:** Đội CSKH của Edmicro.

- **Mục tiêu:** xử lý ticket từ trung tâm/giáo viên/học sinh nhanh chóng; tái hiện được lỗi người dùng gặp.
- **Điều hệ thống phải làm tốt:** hàng đợi ticket có ngữ cảnh (tenant, user, trang lỗi); đăng nhập thay (impersonation) có ghi audit và giới hạn thời gian; tra cứu trạng thái job chấm AI/thông báo để trả lời người dùng.

## Ma trận persona × nhu cầu chính

| Nhu cầu | student | parent | teacher | assistant | academic_head | manager | owner | it_admin | admin | content_editor | support_agent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Học & làm bài | ●●● | | | | | | | | | | |
| Theo dõi kết quả của con | | ●●● | | | | | | | | | |
| Giao bài & theo dõi | | | ●●● | ●● | ●● | ●● | ● | | | | |
| Chấm bài | | | ●●● | ●● | ●● | ● | | | | | |
| Duyệt nội dung chuyên môn | | | | | ●●● | ●● | ● | | | | |
| Báo cáo | ● | ●● | ●● | ● | ●● | ●●● | ●●● | | ● | | |
| Soạn nội dung | | | ●● | | ●●● | ● | | | | ●●● | |
| Quản lý tài khoản & phân lớp | | | ● | | | ●● | ●● | ●●● | | | |
| Quyền trung tâm (cấu hình, kênh, gói) | | | | | | | ●●● | | ●● | | |
| Vận hành nền tảng | | | | | | | | | ●●● | ● | ●●● |

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-16 | Tạo bản nháp đầu tiên | Claude |
| 2026-07-16 | Thêm vai trò IT trung tâm (`it_admin`) theo yêu cầu chủ sản phẩm | Claude |
| 2026-07-16 | Chốt — chuyển trạng thái Đã chốt | Chủ sản phẩm |
| 2026-07-16 | Tách `owner`/`manager`, thêm `academic_head` + `parent` — 11 personas | Chủ sản phẩm |
